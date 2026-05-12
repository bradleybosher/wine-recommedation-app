import React from 'react';
import { MEAL_DESCRIPTION } from './constants';

const COOKING_KEYWORDS = [
  'grilled', 'roasted', 'braised', 'pan-seared', 'seared', 'baked', 'fried',
  'steamed', 'poached', 'smoked', 'cured', 'raw', 'sauce', 'cream', 'butter',
  'herb', 'spice', 'lemon', 'garlic', 'olive oil', 'vinaigrette', 'glaze',
  'reduction', 'seasoned', 'marinated', 'stuffed', 'caramelized', 'crispy',
];

type MealQuality = 'low' | 'medium' | 'high';

function getMealQuality(text: string): MealQuality {
  const lower = text.toLowerCase().trim();
  if (lower.length === 0) return 'low';
  const hasKeyword = COOKING_KEYWORDS.some((k) => lower.includes(k));
  if (lower.length >= 50 && hasKeyword) return 'high';
  if (lower.length >= 20 || hasKeyword) return 'medium';
  return 'low';
}

const QUALITY_CONFIG: Record<MealQuality, { label: string; hint: string | null; bars: [string, string, string] }> = {
  low: {
    label: 'Low',
    hint: 'Add cooking method and sauce for better pairing accuracy.',
    bars: ['bg-wine-rose/80', 'bg-white/15', 'bg-white/15'],
  },
  medium: {
    label: 'Medium',
    hint: 'Try adding sauce, cooking style, or sides for more precise matches.',
    bars: ['bg-wine-amber/80', 'bg-wine-amber/80', 'bg-white/15'],
  },
  high: {
    label: 'High',
    hint: null,
    bars: ['bg-wine-gold/90', 'bg-wine-gold/90', 'bg-wine-gold/90'],
  },
};

const MealDescriptionInput = ({ mealDescription, onMealDescriptionChange, error }) => {
  const handleChange = (e) => {
    const value = e.target.value;
    if (value.length <= MEAL_DESCRIPTION.MAX_CHARS) {
      onMealDescriptionChange(value);
    }
  };

  const quality = getMealQuality(mealDescription);
  const config = QUALITY_CONFIG[quality];
  const showMeter = mealDescription.trim().length > 0;

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
        aria-describedby="meal-description-counter meal-quality-hint"
      ></textarea>
      <div className="flex items-center justify-between mt-1.5 gap-3">
        {showMeter ? (
          <div className="flex items-center gap-2">
            <span className="text-xs text-white/50">Meal detail:</span>
            <div className="flex items-center gap-0.5">
              {config.bars.map((cls, i) => (
                <div key={i} className={`h-1.5 w-5 rounded-full ${cls} transition-colors duration-200`} />
              ))}
            </div>
            <span className="text-xs text-white/60">{config.label}</span>
          </div>
        ) : (
          <div />
        )}
        <div id="meal-description-counter" className="text-sm text-white/50 text-right shrink-0">
          {mealDescription.length}/{MEAL_DESCRIPTION.MAX_CHARS}
        </div>
      </div>
      {showMeter && config.hint && (
        <p id="meal-quality-hint" className="text-xs text-white/50 mt-1">
          {config.hint}
        </p>
      )}
    </div>
  );
};

export default MealDescriptionInput;
