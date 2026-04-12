import React from 'react';
import { MEAL_DESCRIPTION } from './constants';

const MealDescriptionInput = ({ mealDescription, onMealDescriptionChange, error }) => {
  const handleChange = (e) => {
    const value = e.target.value;
    if (value.length <= MEAL_DESCRIPTION.MAX_CHARS) {
      onMealDescriptionChange(value);
    }
  };

  return (
    <div>
      <label htmlFor="meal-description" className="block text-lg font-medium text-white/80 mb-2">
        What are you eating?
      </label>
      <textarea
        id="meal-description"
        rows={4}
        value={mealDescription}
        onChange={handleChange}
        placeholder="e.g., grilled lamb with rosemary, lemon and ricotta cake, pan-seared scallops"
        maxLength={MEAL_DESCRIPTION.MAX_CHARS}
        className="shadow-sm focus:ring-wine-rose focus:border-wine-rose block w-full sm:text-sm border-glass-border rounded-md p-3 bg-glass-surface text-white placeholder:text-white/40"
        aria-describedby="meal-description-counter"
      ></textarea>
      <div id="meal-description-counter" className="text-sm text-white/50 text-right mt-1">
        {mealDescription.length}/{MEAL_DESCRIPTION.MAX_CHARS} characters
      </div>
    </div>
  );
};

export default MealDescriptionInput;
