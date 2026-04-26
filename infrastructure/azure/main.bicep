// =============================================
// PollMaster Azure Infrastructure
// Bicep Template for Production Deployment
// =============================================

@description('Environment name')
param environment string = 'production'

@description('Location for all resources')
param location string = resourceGroup().location

@description('App Service Plan SKU')
param skuName string = environment == 'production' ? 'P1v2' : 'B1'
param skuTier string = environment == 'production' ? 'PremiumV2' : 'Basic'

// =============================================
// App Service Plan
// =============================================
resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: 'pollmaster-${environment}-plan'
  location: location
  sku: {
    name: skuName
    tier: skuTier
    size: skuName
    family: 'P'
    capacity: environment == 'production' ? 2 : 1
  }
  kind: 'linux'
  properties: {
    reserved: true
    perSiteScaling: false
    targetWorkerCount: 0
    targetWorkerSizeId: 0
  }
}

// =============================================
// App Service
// =============================================
resource appService 'Microsoft.Web/sites@2022-03-01' = {
  name: environment == 'production' ? 'pollmaster-bhogarai' : 'pollmaster-${environment}'
  location: location
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'NODE|20-lts'
      alwaysOn: true
      httpLoggingEnabled: true
      detailedErrorLoggingEnabled: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      scmMinTlsVersion: '1.2'
      healthCheckPath: '/health'
      appSettings: [
        {
          name: 'NODE_ENV'
          value: environment
        }
        {
          name: 'WEBSITE_NODE_DEFAULT_VERSION'
          value: '~20'
        }
        {
          name: 'DATABASE_URL'
          value: '@Microsoft.KeyVault(VaultName=pollmaster-kv;SecretName=database-url)'
        }
        {
          name: 'REDIS_URL'
          value: '@Microsoft.KeyVault(VaultName=pollmaster-kv;SecretName=redis-url)'
        }
        {
          name: 'SESSION_SECRET'
          value: '@Microsoft.KeyVault(VaultName=pollmaster-kv;SecretName=session-secret)'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'WEBSITE_HEALTHCHECK_MAXPINGFAILURES'
          value: '3'
        }
      ]
    }
  }
}

// =============================================
// SQL Server
// =============================================
resource sqlServer 'Microsoft.Sql/servers@2022-05-01-preview' = {
  name: 'pollmaster-${environment}-sql'
  location: location
  properties: {
    administratorLogin: 'sqladmin'
    administratorLoginPassword: '@Microsoft.KeyVault(VaultName=pollmaster-kv;SecretName=sql-admin-password)'
    version: '12.0'
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

// SQL Database
resource sqlDatabase 'Microsoft.Sql/servers/databases@2022-05-01-preview' = {
  name: 'pollmaster-db'
  parent: sqlServer
  location: location
  sku: {
    name: environment == 'production' ? 'GP_Gen5_2' : 'GP_Gen5'
    tier: 'GeneralPurpose'
    family: 'Gen5'
    capacity: environment == 'production' ? 2 : 1
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 2147483648
    zoneRedundant: environment == 'production'
    licenseType: 'LicenseIncluded'
    readScale: environment == 'production' ? 'Enabled' : 'Disabled'
  }
}

// Firewall rule for Azure services
resource sqlFirewallRule 'Microsoft.Sql/servers/firewallRules@2022-05-01-preview' = {
  name: 'AllowAllAzureIPs'
  parent: sqlServer
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// =============================================
// Redis Cache
// =============================================
resource redisCache 'Microsoft.Cache/redis@2022-06-01' = {
  name: 'pollmaster-${environment}-redis'
  location: location
  properties: {
    sku: {
      name: environment == 'production' ? 'Standard' : 'Basic'
      family: 'C'
      capacity: 1
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    redisConfiguration: {
      'maxmemory-policy': 'allkeys-lru'
    }
  }
}

// =============================================
// Application Insights
// =============================================
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'pollmaster-${environment}-insights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Flow_Type: 'Bluefield'
    Request_Source: 'rest'
    RetentionInDays: 90
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// =============================================
// Log Analytics Workspace
// =============================================
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'pollmaster-${environment}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// =============================================
// Key Vault
// =============================================
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: 'pollmaster-${environment}-kv'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
  }
}

// =============================================
// Auto-scaling Configuration (Production only)
// =============================================
resource autoScaleSettings 'Microsoft.Insights/autoscalesettings@2022-10-01' = if (environment == 'production') {
  name: 'pollmaster-autoscale'
  location: location
  properties: {
    targetResourceUri: appServicePlan.id
    enabled: true
    profiles: [
      {
        name: 'Auto-scale'
        capacity: {
          minimum: '2'
          maximum: '10'
          default: '2'
        }
        rules: [
          {
            metricTrigger: {
              metricName: 'CpuPercentage'
              metricResourceUri: appServicePlan.id
              timeGrain: 'PT1M'
              statistic: 'Average'
              timeWindow: 'PT5M'
              timeAggregation: 'Average'
              operator: 'GreaterThan'
              threshold: 70
            }
            scaleAction: {
              direction: 'Increase'
              type: 'ChangeCount'
              value: '2'
              cooldown: 'PT5M'
            }
          }
          {
            metricTrigger: {
              metricName: 'CpuPercentage'
              metricResourceUri: appServicePlan.id
              timeGrain: 'PT1M'
              statistic: 'Average'
              timeWindow: 'PT5M'
              timeAggregation: 'Average'
              operator: 'LessThan'
              threshold: 30
            }
            scaleAction: {
              direction: 'Decrease'
              type: 'ChangeCount'
              value: '1'
              cooldown: 'PT5M'
            }
          }
        ]
      }
    ]
  }
}

// =============================================
// Outputs
// =============================================
output appServiceUrl string = 'https://${appService.properties.defaultHostName}'
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
output redisHostName string = redisCache.properties.hostName
output appInsightsKey string = appInsights.properties.InstrumentationKey
