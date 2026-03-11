import { useCategoryLanguage } from '@/contexts/CategoryLanguageContext';
import type { Category } from '@/types';

export const useCategoryLabel = () => {
  const { categoryLanguage } = useCategoryLanguage();

  const getCategoryLabel = (cat: Category): string =>
    categoryLanguage === 'pt' && cat.description_translated
      ? cat.description_translated
      : cat.description;

  return { getCategoryLabel };
};

export const useCategoryLabelByName = (catByDescription: Map<string, Category>) => {
  const { getCategoryLabel } = useCategoryLabel();

  return (name: string): string => {
    const cat = catByDescription.get(name);
    return cat ? getCategoryLabel(cat) : name;
  };
};
