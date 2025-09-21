import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, X } from 'lucide-react';
import { suggestionService } from '../services/suggestionService';

interface AutocompleteInputProps {
  name: string;
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  placeholder?: string;
  className?: string;
  required?: boolean;
  disabled?: boolean;
  maxSuggestions?: number;
}

const AutocompleteInput: React.FC<AutocompleteInputProps> = ({
  name,
  value,
  onChange,
  onBlur,
  placeholder,
  className = 'form-input',
  required = false,
  disabled = false,
  maxSuggestions = 5
}) => {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [inputFocused, setInputFocused] = useState(false);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Load suggestions when component mounts or value changes
  useEffect(() => {
    const filteredSuggestions = suggestionService
      .filterSuggestions(name, value)
      .slice(0, maxSuggestions);
    
    setSuggestions(filteredSuggestions);
    setSelectedIndex(-1);
  }, [name, value, maxSuggestions]);

  // Handle input focus
  const handleFocus = () => {
    setInputFocused(true);
    if (suggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  // Handle input blur with delay to allow for suggestion clicks
  const handleBlur = () => {
    setTimeout(() => {
      setInputFocused(false);
      setShowSuggestions(false);
      setSelectedIndex(-1);
      if (onBlur) {
        onBlur();
      }
    }, 150);
  };

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
    
    // Show suggestions if there are any and input is focused
    if (newValue.trim() && inputFocused) {
      setShowSuggestions(suggestions.length > 0);
    } else if (!newValue.trim()) {
      setShowSuggestions(false);
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions || suggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        break;
      
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;
      
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          selectSuggestion(suggestions[selectedIndex]);
        }
        break;
      
      case 'Escape':
        e.preventDefault();
        setShowSuggestions(false);
        setSelectedIndex(-1);
        inputRef.current?.blur();
        break;
    }
  };

  // Handle suggestion selection
  const selectSuggestion = (suggestion: string) => {
    onChange(suggestion);
    setShowSuggestions(false);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  };

  // Clear input
  const clearInput = () => {
    onChange('');
    setShowSuggestions(false);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  };

  return (
    <div className="relative">
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          name={name}
          value={value}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className={`${className} ${value ? 'pr-12' : ''}`}
          required={required}
          disabled={disabled}
          autoComplete="off"
        />
        
        {/* Clear button */}
        {value && !disabled && (
          <button
            type="button"
            onClick={clearInput}
            className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors p-1"
            tabIndex={-1}
          >
            <X className="w-4 h-4" />
          </button>
        )}
        
        {/* Dropdown indicator */}
        {suggestions.length > 0 && !value && (
          <div className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400">
            <ChevronDown className="w-4 h-4" />
          </div>
        )}
      </div>

      {/* Suggestions dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto"
        >
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              type="button"
              className={`w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-b-0 ${
                index === selectedIndex ? 'bg-blue-50 text-blue-700' : 'text-gray-800'
              }`}
              onClick={() => selectSuggestion(suggestion)}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <div className="truncate">
                {suggestion}
              </div>
            </button>
          ))}
          
          {/* Show count if there are more suggestions available */}
          {suggestionService.getSuggestions(name).length > maxSuggestions && (
            <div className="px-4 py-2 text-xs text-gray-500 bg-gray-50 border-t border-gray-200">
              Showing {maxSuggestions} of {suggestionService.getSuggestions(name).length} suggestions
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AutocompleteInput;