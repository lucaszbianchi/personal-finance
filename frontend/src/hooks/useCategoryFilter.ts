import { useState, useMemo } from 'react';
import type { Category } from '@/types';

export const useCategoryFilter = (categoriesList: Category[]) => {
  const [parentFilter, setParentFilter] = useState<string>('__all__');

  const catByDescription = useMemo(() => {
    const map = new Map<string, Category>();
    categoriesList.forEach(cat => map.set(cat.description, cat));
    return map;
  }, [categoriesList]);

  const uniqueParents = useMemo(() => {
    const groups = new Set(
      categoriesList.map(cat => cat.parent_description).filter(Boolean) as string[]
    );
    return Array.from(groups).sort();
  }, [categoriesList]);

  const filteredCategories = useMemo(() => {
    if (parentFilter === '__all__') return categoriesList;
    return categoriesList.filter(
      cat => cat.parent_description === parentFilter || cat.description === parentFilter
    );
  }, [categoriesList, parentFilter]);

  const resetFilter = () => setParentFilter('__all__');

  return { parentFilter, setParentFilter, catByDescription, uniqueParents, filteredCategories, resetFilter };
};
