import React, { createContext, useContext, useState } from 'react';

type CategoryLanguage = 'en' | 'pt';

interface CategoryLanguageContextValue {
  categoryLanguage: CategoryLanguage;
  setCategoryLanguage: (lang: CategoryLanguage) => void;
}

const CategoryLanguageContext = createContext<CategoryLanguageContextValue | null>(null);

export const CategoryLanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [categoryLanguage, setCategoryLanguageState] = useState<CategoryLanguage>(() => {
    const stored = localStorage.getItem('category_language');
    return stored === 'pt' ? 'pt' : 'en';
  });

  const setCategoryLanguage = (lang: CategoryLanguage) => {
    localStorage.setItem('category_language', lang);
    setCategoryLanguageState(lang);
  };

  return (
    <CategoryLanguageContext.Provider value={{ categoryLanguage, setCategoryLanguage }}>
      {children}
    </CategoryLanguageContext.Provider>
  );
};

export const useCategoryLanguage = (): CategoryLanguageContextValue => {
  const ctx = useContext(CategoryLanguageContext);
  if (!ctx) throw new Error('useCategoryLanguage must be used inside CategoryLanguageProvider');
  return ctx;
};
