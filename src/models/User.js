/**
 * User Model
 * Represents a user account in the PollMaster system
 */

const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');

class User {
  constructor(data = {}) {
    this.id = data.id || uuidv4();
    this.email = data.email || '';
    this.passwordHash = data.password_hash || data.passwordHash || '';
    this.username = data.username || '';
    this.firstName = data.first_name || data.firstName || null;
    this.lastName = data.last_name || data.lastName || null;
    this.avatarUrl = data.avatar_url || data.avatarUrl || null;
    this.isActive = data.is_active !== undefined ? data.is_active : true;
    this.isEmailVerified = data.is_email_verified !== undefined ? data.is_email_verified : false;
    this.tokenVersion = data.token_version || data.tokenVersion || 1;
    this.lastLoginAt = data.last_login_at || data.lastLoginAt || null;
    this.createdAt = data.created_at || data.createdAt || new Date();
    this.updatedAt = data.updated_at || data.updatedAt || new Date();
  }

  /**
   * Validate password against stored hash
   * @param {string} password - Plain text password
   * @returns {Promise<boolean>} - Whether password matches
   */
  async validatePassword(password) {
    if (!this.passwordHash) return false;
    return bcrypt.compare(password, this.passwordHash);
  }

  /**
   * Generate JWT tokens for authentication
   * @returns {Object} - Access and refresh tokens
   */
  generateAuthToken() {
    const accessToken = jwt.sign(
      {
        sub: this.id,
        email: this.email,
        username: this.username,
        role: 'user'
      },
      process.env.JWT_ACCESS_SECRET,
      {
        expiresIn: '15m',
        issuer: 'pollmaster-api',
        audience: 'pollmaster-client'
      }
    );

    const refreshToken = jwt.sign(
      {
        sub: this.id,
        tokenVersion: this.tokenVersion
      },
      process.env.JWT_REFRESH_SECRET,
      {
        expiresIn: '7d',
        issuer: 'pollmaster-api',
        audience: 'pollmaster-client'
      }
    );

    return {
      accessToken,
      refreshToken,
      expiresIn: 900 // 15 minutes in seconds
    };
  }

  /**
   * Update last login timestamp
   */
  updateLastLogin() {
    this.lastLoginAt = new Date();
  }

  /**
   * Get full name
   * @returns {string} - Full name or username
   */
  getFullName() {
    if (this.firstName && this.lastName) {
      return `${this.firstName} ${this.lastName}`;
    }
    return this.firstName || this.lastName || this.username;
  }

  /**
   * Convert to JSON (excludes sensitive fields)
   * @returns {Object} - User data without password
   */
  toJSON() {
    return {
      id: this.id,
      email: this.email,
      username: this.username,
      firstName: this.firstName,
      lastName: this.lastName,
      avatarUrl: this.avatarUrl,
      isActive: this.isActive,
      isEmailVerified: this.isEmailVerified,
      lastLoginAt: this.lastLoginAt,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt
    };
  }

  /**
   * Convert to database format
   * @returns {Object} - Database-ready object
   */
  toDatabase() {
    return {
      id: this.id,
      email: this.email,
      password_hash: this.passwordHash,
      username: this.username,
      first_name: this.firstName,
      last_name: this.lastName,
      avatar_url: this.avatarUrl,
      is_active: this.isActive,
      is_email_verified: this.isEmailVerified,
      token_version: this.tokenVersion,
      last_login_at: this.lastLoginAt,
      created_at: this.createdAt,
      updated_at: this.updatedAt
    };
  }

  // Static methods

  /**
   * Hash a password
   * @param {string} password - Plain text password
   * @returns {Promise<string>} - Hashed password
   */
  static async hashPassword(password) {
    const saltRounds = 12;
    return bcrypt.hash(password, saltRounds);
  }

  /**
   * Create a new user instance from input data
   * @param {Object} data - User creation data
   * @returns {Promise<User>} - New user instance
   */
  static async create(data) {
    const passwordHash = await User.hashPassword(data.password);
    
    return new User({
      email: data.email,
      passwordHash,
      username: data.username,
      firstName: data.firstName,
      lastName: data.lastName
    });
  }

  /**
   * Validate user creation input
   * @param {Object} data - Input data
   * @returns {Object} - Validation result
   */
  static validateCreateInput(data) {
    const errors = [];

    // Email validation
    if (!data.email) {
      errors.push({ field: 'email', message: 'Email is required' });
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
      errors.push({ field: 'email', message: 'Invalid email format' });
    } else if (data.email.length > 255) {
      errors.push({ field: 'email', message: 'Email must be less than 255 characters' });
    }

    // Password validation
    if (!data.password) {
      errors.push({ field: 'password', message: 'Password is required' });
    } else {
      if (data.password.length < 8) {
        errors.push({ field: 'password', message: 'Password must be at least 8 characters' });
      }
      if (data.password.length > 128) {
        errors.push({ field: 'password', message: 'Password must be less than 128 characters' });
      }
      if (!/[A-Z]/.test(data.password)) {
        errors.push({ field: 'password', message: 'Password must contain at least one uppercase letter' });
      }
      if (!/[a-z]/.test(data.password)) {
        errors.push({ field: 'password', message: 'Password must contain at least one lowercase letter' });
      }
      if (!/[0-9]/.test(data.password)) {
        errors.push({ field: 'password', message: 'Password must contain at least one number' });
      }
      if (!/[!@#$%^&*]/.test(data.password)) {
        errors.push({ field: 'password', message: 'Password must contain at least one special character' });
      }
    }

    // Username validation
    if (!data.username) {
      errors.push({ field: 'username', message: 'Username is required' });
    } else {
      if (data.username.length < 3) {
        errors.push({ field: 'username', message: 'Username must be at least 3 characters' });
      }
      if (data.username.length > 50) {
        errors.push({ field: 'username', message: 'Username must be less than 50 characters' });
      }
      if (!/^[a-zA-Z0-9_]+$/.test(data.username)) {
        errors.push({ field: 'username', message: 'Username can only contain letters, numbers, and underscores' });
      }
    }

    // Optional fields validation
    if (data.firstName && data.firstName.length > 100) {
      errors.push({ field: 'firstName', message: 'First name must be less than 100 characters' });
    }
    if (data.lastName && data.lastName.length > 100) {
      errors.push({ field: 'lastName', message: 'Last name must be less than 100 characters' });
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }
}

module.exports = User;
