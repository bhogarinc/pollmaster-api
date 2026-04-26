/**
 * Poll Model
 * Represents a poll in the PollMaster system
 */

const { v4: uuidv4 } = require('uuid');
const crypto = require('crypto');

class Poll {
  constructor(data = {}) {
    this.id = data.id || uuidv4();
    this.title = data.title || '';
    this.description = data.description || null;
    this.creatorId = data.creator_id || data.creatorId || null;
    this.uniqueLink = data.unique_link || data.uniqueLink || this.generateUniqueLink();
    this.isActive = data.is_active !== undefined ? data.is_active : true;
    this.isPublic = data.is_public !== undefined ? data.is_public : true;
    this.allowMultipleVotes = data.allow_multiple_votes !== undefined ? data.allow_multiple_votes : false;
    this.allowAnonymousVotes = data.allow_anonymous_votes !== undefined ? data.allow_anonymous_votes : true;
    this.showResultsBeforeVoting = data.show_results_before_voting !== undefined ? data.show_results_before_voting : false;
    this.showResultsAfterVoting = data.show_results_after_voting !== undefined ? data.show_results_after_voting : true;
    this.expiresAt = data.expires_at || data.expiresAt || null;
    this.totalVotes = data.total_votes || data.totalVotes || 0;
    this.viewCount = data.view_count || data.viewCount || 0;
    this.createdAt = data.created_at || data.createdAt || new Date();
    this.updatedAt = data.updated_at || data.updatedAt || new Date();
    this.deletedAt = data.deleted_at || data.deletedAt || null;

    // Relationships (populated separately)
    this.creator = data.creator || null;
    this.questions = data.questions || [];
    this.votes = data.votes || [];
  }

  /**
   * Check if poll has expired
   * @returns {boolean} - Whether poll has expired
   */
  isExpired() {
    if (!this.isActive) return true;
    if (this.expiresAt && new Date(this.expiresAt) < new Date()) return true;
    return false;
  }

  /**
   * Check if poll is visible to a user
   * @param {User|null} user - User to check visibility for
   * @returns {boolean} - Whether poll is visible
   */
  isVisibleTo(user) {
    if (this.isPublic) return true;
    if (user && user.id === this.creatorId) return true;
    return false;
  }

  /**
   * Check if user can vote in this poll
   * @param {User|null} user - User attempting to vote
   * @param {string} fingerprint - Voter fingerprint
   * @returns {Object} - Can vote result with reason
   */
  canVote(user, fingerprint) {
    if (this.isExpired()) {
      return { canVote: false, reason: 'POLL_EXPIRED' };
    }

    if (!this.isActive) {
      return { canVote: false, reason: 'POLL_INACTIVE' };
    }

    // Additional checks would be done in VoteService for duplicate votes
    return { canVote: true };
  }

  /**
   * Generate a unique link for the poll
   * @param {number} length - Length of the link
   * @returns {string} - Unique link
   */
  generateUniqueLink(length = 10) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    const randomBytes = crypto.randomBytes(length);
    
    for (let i = 0; i < length; i++) {
      result += chars[randomBytes[i] % chars.length];
    }
    
    return result;
  }

  /**
   * Increment view count
   */
  incrementViewCount() {
    this.viewCount++;
  }

  /**
   * Get share URL
   * @returns {string} - Full share URL
   */
  getShareUrl() {
    const baseUrl = process.env.APP_URL || 'https://pollmaster.app';
    return `${baseUrl}/p/${this.uniqueLink}`;
  }

  /**
   * Create a duplicate of this poll
   * @param {string} newCreatorId - ID of the new creator
   * @returns {Poll} - New poll instance
   */
  duplicate(newCreatorId) {
    const newPoll = new Poll({
      title: `${this.title} (Copy)`,
      description: this.description,
      creatorId: newCreatorId,
      isPublic: this.isPublic,
      allowMultipleVotes: this.allowMultipleVotes,
      allowAnonymousVotes: this.allowAnonymousVotes,
      showResultsBeforeVoting: this.showResultsBeforeVoting,
      showResultsAfterVoting: this.showResultsAfterVoting,
      isActive: true,
      expiresAt: null // Reset expiration
    });

    // Copy questions structure (without IDs and vote counts)
    newPoll.questions = this.questions.map(q => ({
      text: q.text,
      questionType: q.questionType,
      isRequired: q.isRequired,
      orderIndex: q.orderIndex,
      options: q.options.map(o => ({
        text: o.text,
        orderIndex: o.orderIndex
      }))
    }));

    return newPoll;
  }

  /**
   * Convert to JSON
   * @returns {Object} - Poll data
   */
  toJSON() {
    return {
      id: this.id,
      title: this.title,
      description: this.description,
      uniqueLink: this.uniqueLink,
      shareUrl: this.getShareUrl(),
      isActive: this.isActive,
      isPublic: this.isPublic,
      allowMultipleVotes: this.allowMultipleVotes,
      allowAnonymousVotes: this.allowAnonymousVotes,
      showResultsBeforeVoting: this.showResultsBeforeVoting,
      showResultsAfterVoting: this.showResultsAfterVoting,
      expiresAt: this.expiresAt,
      totalVotes: this.totalVotes,
      viewCount: this.viewCount,
      creator: this.creator ? this.creator.toJSON() : null,
      questions: this.questions.map(q => ({
        id: q.id,
        text: q.text,
        questionType: q.questionType,
        isRequired: q.isRequired,
        orderIndex: q.orderIndex,
        options: q.options.map(o => ({
          id: o.id,
          text: o.text,
          orderIndex: o.orderIndex,
          voteCount: o.voteCount
        }))
      })),
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
      title: this.title,
      description: this.description,
      creator_id: this.creatorId,
      unique_link: this.uniqueLink,
      is_active: this.isActive,
      is_public: this.isPublic,
      allow_multiple_votes: this.allowMultipleVotes,
      allow_anonymous_votes: this.allowAnonymousVotes,
      show_results_before_voting: this.showResultsBeforeVoting,
      show_results_after_voting: this.showResultsAfterVoting,
      expires_at: this.expiresAt,
      total_votes: this.totalVotes,
      view_count: this.viewCount,
      created_at: this.createdAt,
      updated_at: this.updatedAt,
      deleted_at: this.deletedAt
    };
  }

  // Static methods

  /**
   * Validate poll creation input
   * @param {Object} data - Input data
   * @returns {Object} - Validation result
   */
  static validateCreateInput(data) {
    const errors = [];

    // Title validation
    if (!data.title) {
      errors.push({ field: 'title', message: 'Title is required' });
    } else {
      if (data.title.length < 3) {
        errors.push({ field: 'title', message: 'Title must be at least 3 characters' });
      }
      if (data.title.length > 255) {
        errors.push({ field: 'title', message: 'Title must be less than 255 characters' });
      }
    }

    // Description validation
    if (data.description && data.description.length > 2000) {
      errors.push({ field: 'description', message: 'Description must be less than 2000 characters' });
    }

    // Questions validation
    if (!data.questions || !Array.isArray(data.questions) || data.questions.length === 0) {
      errors.push({ field: 'questions', message: 'At least one question is required' });
    } else if (data.questions.length > 50) {
      errors.push({ field: 'questions', message: 'Maximum 50 questions allowed' });
    } else {
      data.questions.forEach((question, index) => {
        if (!question.text) {
          errors.push({ field: `questions[${index}].text`, message: 'Question text is required' });
        } else if (question.text.length > 1000) {
          errors.push({ field: `questions[${index}].text`, message: 'Question text must be less than 1000 characters' });
        }

        if (!question.options || !Array.isArray(question.options) || question.options.length < 2) {
          errors.push({ field: `questions[${index}].options`, message: 'At least 2 options are required' });
        } else if (question.options.length > 20) {
          errors.push({ field: `questions[${index}].options`, message: 'Maximum 20 options allowed per question' });
        } else {
          question.options.forEach((option, optIndex) => {
            if (!option.text) {
              errors.push({ field: `questions[${index}].options[${optIndex}].text`, message: 'Option text is required' });
            } else if (option.text.length > 500) {
              errors.push({ field: `questions[${index}].options[${optIndex}].text`, message: 'Option text must be less than 500 characters' });
            }
          });
        }
      });
    }

    // Expiration validation
    if (data.expiresAt) {
      const expiresAt = new Date(data.expiresAt);
      if (isNaN(expiresAt.getTime())) {
        errors.push({ field: 'expiresAt', message: 'Invalid expiration date' });
      } else if (expiresAt < new Date()) {
        errors.push({ field: 'expiresAt', message: 'Expiration date must be in the future' });
      }
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }
}

module.exports = Poll;
