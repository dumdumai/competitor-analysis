/**
 * Service for managing form field suggestions using localStorage
 */

interface SuggestionData {
  [key: string]: string[];
}

class SuggestionService {
  private readonly STORAGE_KEY = 'form_suggestions';
  private readonly MAX_SUGGESTIONS = 10;

  /**
   * Get suggestions for a specific field
   */
  getSuggestions(fieldName: string): string[] {
    try {
      const suggestions = this.getAllSuggestions();
      return suggestions[fieldName] || [];
    } catch (error) {
      console.error('Error getting suggestions:', error);
      return [];
    }
  }

  /**
   * Add a new suggestion for a field
   */
  addSuggestion(fieldName: string, value: string): void {
    try {
      if (!value || !value.trim()) return;

      const trimmedValue = value.trim();
      const suggestions = this.getAllSuggestions();
      
      if (!suggestions[fieldName]) {
        suggestions[fieldName] = [];
      }

      // Remove if already exists to avoid duplicates
      suggestions[fieldName] = suggestions[fieldName].filter(
        item => item.toLowerCase() !== trimmedValue.toLowerCase()
      );

      // Add to beginning of array
      suggestions[fieldName].unshift(trimmedValue);

      // Keep only the most recent MAX_SUGGESTIONS items
      if (suggestions[fieldName].length > this.MAX_SUGGESTIONS) {
        suggestions[fieldName] = suggestions[fieldName].slice(0, this.MAX_SUGGESTIONS);
      }

      this.saveSuggestions(suggestions);
    } catch (error) {
      console.error('Error adding suggestion:', error);
    }
  }

  /**
   * Get all suggestions from localStorage
   */
  private getAllSuggestions(): SuggestionData {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      return stored ? JSON.parse(stored) : {};
    } catch (error) {
      console.error('Error parsing suggestions from localStorage:', error);
      return {};
    }
  }

  /**
   * Save suggestions to localStorage
   */
  private saveSuggestions(suggestions: SuggestionData): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(suggestions));
    } catch (error) {
      console.error('Error saving suggestions to localStorage:', error);
    }
  }

  /**
   * Filter suggestions based on current input
   */
  filterSuggestions(fieldName: string, currentValue: string): string[] {
    const allSuggestions = this.getSuggestions(fieldName);
    
    if (!currentValue || !currentValue.trim()) {
      return allSuggestions;
    }

    const searchTerm = currentValue.toLowerCase().trim();
    return allSuggestions.filter(suggestion =>
      suggestion.toLowerCase().includes(searchTerm) &&
      suggestion.toLowerCase() !== searchTerm
    );
  }

  /**
   * Clear all suggestions (for testing/debugging)
   */
  clearAllSuggestions(): void {
    try {
      localStorage.removeItem(this.STORAGE_KEY);
    } catch (error) {
      console.error('Error clearing suggestions:', error);
    }
  }

  /**
   * Save form data for suggestions when form is submitted
   */
  saveFormData(formData: Record<string, any>): void {
    const fieldsToSave = [
      'client_company',
      'industry', 
      'target_market',
      'business_model',
      'specific_requirements'
    ];

    fieldsToSave.forEach(fieldName => {
      if (formData[fieldName]) {
        this.addSuggestion(fieldName, formData[fieldName]);
      }
    });
  }
}

export const suggestionService = new SuggestionService();
export default suggestionService;