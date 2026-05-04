import {
  getInventoryInventoryGet,
  profileSummaryProfileSummaryGet,
} from '@/client';

// DEPRECATED: Use SDK functions directly from '@/client'
// These functions are kept for temporary backward compatibility

export const submitRecommendationRequest = async (payload: any): Promise<any> => {
  console.warn('submitRecommendationRequest is deprecated. Use recommendRecommendPost from SDK directly.');
  throw new Error('submitRecommendationRequest is deprecated. Use recommendRecommendPost from SDK directly.');
};

export const preparePayload = (imageBase64: string, mealDescription: string, styleOverrides: string): any => {
  console.warn('preparePayload is deprecated. Create request body according to SDK types.');
  const styleOverridesArray = styleOverrides.split(',').map((s: string) => s.trim()).filter((s: string) => s);

  return {
    image_base64: imageBase64,
    meal_description: mealDescription.trim(),
    style_overrides: styleOverridesArray,
  };
};

export const fetchInventoryStatus = async (): Promise<any> => {
  try {
    const response = await getInventoryInventoryGet();
    const sdkData = response.data;

    return {
      count: sdkData.bottles?.length || 0,
      bottles: sdkData.bottles?.map(bottle => ({
        wine_name: bottle.wine || '',
        producer: bottle.producer || '',
        vintage: bottle.vintage || '',
        region: bottle.region || ''
      })) || [],
      stale_flag: sdkData.stale || false
    };
  } catch (error: any) {
    if (error.data?.detail) {
      throw new Error(error.data.detail);
    }
    throw error;
  }
};

export const fetchProfileSummary = async (): Promise<any> => {
  try {
    const response = await profileSummaryProfileSummaryGet();
    const sdkData = response.data;

    const result: any = {};
    if (sdkData.topVarietals) result.top_varietals = sdkData.topVarietals;
    if (sdkData.topRegions) result.top_regions = sdkData.topRegions;
    if (sdkData.topProducers) result.top_producers = sdkData.topProducers;
    if (sdkData.highlyRated) result.highly_rated = sdkData.highlyRated;
    if (sdkData.preferredDescriptors) result.preferred_descriptors = sdkData.preferredDescriptors;
    if (sdkData.avoidedStyles) result.avoided_styles = sdkData.avoidedStyles;
    if (sdkData.avgSpend !== undefined) result.avg_spend = sdkData.avgSpend;

    return result;
  } catch (error: any) {
    if (error.data?.detail) {
      throw new Error(error.data.detail);
    }
    throw error;
  }
};

export const fetchPalatePortrait = async (): Promise<any> => {
  try {
    const response = await profileSummaryProfileSummaryGet();
    const sdkData = response.data;

    return {
      portrait: `Palate portrait based on your profile:\n\nTop varietals: ${(sdkData.topVarietals || []).join(', ')}\nTop regions: ${(sdkData.topRegions || []).join(', ')}\nPreferred descriptors: ${(sdkData.preferredDescriptors || []).join(', ')}`,
      profile_summary: {
        total_consumed: 0,
        tasting_notes_count: 0,
        derived_taste_profile: {
          top_varietals: sdkData.topVarietals || [],
          top_regions: sdkData.topRegions || []
        }
      }
    };
  } catch (error: any) {
    if (error.data?.detail) {
      throw new Error(error.data.detail);
    }
    throw error;
  }
};
