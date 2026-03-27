import React, { useState } from 'react';
import { useCategories, useCreateCategory, useUpdateCategory, useUpdateCategoryFields, useDeleteCategory, useUnifyCategories } from '@/hooks/useCategories';
import { useCategoryLabel } from '@/hooks/useCategoryLabel';
import { useCategoryFilter } from '@/hooks/useCategoryFilter';
import { Plus, Tag, X, Edit, GitMerge, Trash2 } from 'lucide-react';
import type { Category } from '@/types';
import { CategoryPieChart } from '@/components/CategoryPieChart';
import { CategoryExpenseLineChart } from '@/components/CategoryExpenseLineChart';
import { CategorySankeyChart } from '@/components/CategorySankeyChart';
import { AutomationsTab } from '@/components/AutomationsTab';
import { useDashboardData } from '@/hooks/useDashboardData';

type ActiveTab = 'categories' | 'manage' | 'visualizations' | 'automations';
type ExpenseType = 'necessary' | 'optional' | null;

const VisualizationsSection: React.FC = () => {
  const { data: dashboardData } = useDashboardData();
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Gastos por Categoria (mês atual)</h3>
        {dashboardData?.category_breakdown && dashboardData.category_breakdown.length > 0 ? (
          <CategoryPieChart data={dashboardData.category_breakdown} />
        ) : (
          <p className="text-gray-500 text-center py-12">Sem dados de categorias disponíveis.</p>
        )}
      </div>
      <CategoryExpenseLineChart />
      <CategorySankeyChart />
    </div>
  );
};

export const Categories: React.FC = () => {
  const { data: categories, isLoading, error } = useCategories();
  const createCategory = useCreateCategory();
  const updateCategory = useUpdateCategory();
  const updateCategoryFields = useUpdateCategoryFields();
  const deleteCategory = useDeleteCategory();
  const unifyCategories = useUnifyCategories();

  const [activeTab, setActiveTab] = useState<ActiveTab>('categories');

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryParentId, setNewCategoryParentId] = useState<string>('');
  const [newCategoryParentDescription, setNewCategoryParentDescription] = useState<string>('');

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [editCategoryName, setEditCategoryName] = useState('');
  const [editDescriptionTranslated, setEditDescriptionTranslated] = useState('');
  const [editParentId, setEditParentId] = useState<string>('');
  const [editParentDescription, setEditParentDescription] = useState<string>('');
  const [editExpenseType, setEditExpenseType] = useState<string>('');

  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [isDeleteBulkModalOpen, setIsDeleteBulkModalOpen] = useState(false);
  const [bulkDeleteError, setBulkDeleteError] = useState<string>('');

  const [isUnifyModalOpen, setIsUnifyModalOpen] = useState(false);
  const [targetCategory, setTargetCategory] = useState('');

  const { getCategoryLabel } = useCategoryLabel();

  const categoriesList = categories || [];

  const {
    parentFilter: selectedParent,
    setParentFilter: setSelectedParent,
    catByDescription,
    uniqueParents,
    filteredCategories: displayedCategories,
    ungroupedCount,
  } = useCategoryFilter(categoriesList);

  // --- Helpers for parent select ---
  const parentSelectValue = (parentId: string, parentDescription: string) => {
    if (!parentId && !parentDescription) return '';
    if (parentId === '__new__') return '__new__';
    return parentId;
  };

  const handleParentSelectChange = (
    value: string,
    setId: (v: string) => void,
    setDesc: (v: string) => void,
    selfName?: string,
    selfId?: string,
  ) => {
    if (value === '') {
      setId('');
      setDesc('');
    } else if (value === '__new__') {
      // sentinel: will be resolved after save using the category's own id
      setId('__new__');
      setDesc(selfName ?? '');
    } else {
      const cat = categoriesList.find(c => c.id === value);
      setId(cat?.id ?? '');
      setDesc(cat?.description ?? '');
      void selfId; // unused when editing existing parent
    }
  };

  // --- Create ---
  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCategoryName.trim()) return;

    try {
      const isNewGroup = newCategoryParentId === '__new__';
      const created = await createCategory.mutateAsync({
        description: newCategoryName.trim(),
        description_translated: newCategoryName.trim(),
        parent_id: isNewGroup ? null : (newCategoryParentId || null),
        parent_description: isNewGroup ? null : (newCategoryParentDescription || null),
      });
      if (isNewGroup && created?.id) {
        await updateCategoryFields.mutateAsync({
          id: created.id,
          fields: { parent_id: created.id, parent_description: newCategoryName.trim() },
        });
      }
      setNewCategoryName('');
      setNewCategoryParentId('');
      setNewCategoryParentDescription('');
      setIsCreateModalOpen(false);
    } catch (err) {
      console.error('Erro ao criar categoria:', err);
    }
  };

  // --- Edit ---
  const handleEditCategory = (category: Category) => {
    setEditingCategory(category);
    setEditCategoryName(category.description);
    setEditDescriptionTranslated(category.description_translated ?? '');
    setEditParentId(category.parent_id ?? '');
    setEditParentDescription(category.parent_description ?? '');
    setEditExpenseType(category.expense_type ?? '');
    setIsEditModalOpen(true);
  };

  const handleUpdateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCategory || !editCategoryName.trim()) return;

    try {
      let newCategoryId = editingCategory.id;

      if (editCategoryName.trim() !== editingCategory.description) {
        const result = await updateCategory.mutateAsync({
          oldName: editingCategory.description,
          newName: editCategoryName.trim(),
        });
        // backend returns new id
        if (result?.new_id) newCategoryId = result.new_id;
      }

      const isNewGroup = editParentId === '__new__';
      const resolvedParentId = isNewGroup ? newCategoryId : (editParentId || null);
      const resolvedParentDesc = isNewGroup ? editCategoryName.trim() : (editParentDescription || null);

      await updateCategoryFields.mutateAsync({
        id: newCategoryId,
        fields: {
          description_translated: editDescriptionTranslated || null,
          parent_id: resolvedParentId,
          parent_description: resolvedParentDesc,
          expense_type: editExpenseType || null,
        },
      });

      setEditingCategory(null);
      setEditCategoryName('');
      setEditDescriptionTranslated('');
      setEditParentId('');
      setEditParentDescription('');
      setEditExpenseType('');
      setIsEditModalOpen(false);
    } catch (err) {
      console.error('Erro ao editar categoria:', err);
    }
  };

  // --- Bulk delete ---
  const handleBulkDelete = async () => {
    setBulkDeleteError('');
    const errors: string[] = [];
    const failed = new Set<string>();
    for (const name of selectedCategories) {
      try {
        await deleteCategory.mutateAsync(name);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        errors.push(`${name}: ${msg}`);
        failed.add(name);
      }
    }
    if (errors.length > 0) {
      // Remover da seleção apenas as categorias já deletadas com sucesso,
      // mantendo as que falharam para o usuário poder revisar e tentar novamente.
      setSelectedCategories(prev => prev.filter(name => failed.has(name)));
      setBulkDeleteError(errors.join('\n'));
    } else {
      setSelectedCategories([]);
      setIsDeleteBulkModalOpen(false);
    }
  };

  // --- Select ---
  const handleSelectCategory = (categoryName: string) => {
    setSelectedCategories(prev =>
      prev.includes(categoryName)
        ? prev.filter(name => name !== categoryName)
        : [...prev, categoryName]
    );
  };

  const handleSelectAll = () => {
    if (selectedCategories.length === displayedCategories.length && displayedCategories.length > 0) {
      setSelectedCategories([]);
    } else {
      setSelectedCategories(displayedCategories.map(cat => cat.description));
    }
  };

  // --- Unify ---
  const handleOpenUnifyModal = () => {
    if (selectedCategories.length < 2) return;
    setTargetCategory(selectedCategories[0]);
    setIsUnifyModalOpen(true);
  };

  const handleUnifyCategories = async () => {
    if (!targetCategory || selectedCategories.length < 2) return;

    try {
      await unifyCategories.mutateAsync({
        categories: selectedCategories,
        target: targetCategory
      });
      setSelectedCategories([]);
      setTargetCategory('');
      setIsUnifyModalOpen(false);
    } catch (err) {
      console.error('Erro ao unificar categorias:', err);
    }
  };

  const parentCategories = React.useMemo(
    () => uniqueParents.map(desc => catByDescription.get(desc)).filter((c): c is Category => !!c),
    [uniqueParents, catByDescription],
  );

  const childrenByParentId = React.useMemo(() => {
    const map = new Map<string, Category[]>();
    categoriesList.forEach(cat => {
      if (cat.parent_id && cat.parent_id !== cat.id) {
        const list = map.get(cat.parent_id) ?? [];
        list.push(cat);
        map.set(cat.parent_id, list);
      }
    });
    return map;
  }, [categoriesList]);

  const [manageFilter, setManageFilter] = useState<'expenses' | 'all'>('expenses');

  const parentExpenseCount = React.useMemo(() => {
    const counts = new Map<string, number>();
    parentCategories.forEach(cat => {
      const children = childrenByParentId.get(cat.id) ?? [];
      const total = cat.expense_transaction_count
        + children.reduce((s, c) => s + c.expense_transaction_count, 0);
      counts.set(cat.id, total);
    });
    return counts;
  }, [parentCategories, childrenByParentId]);

  const filteredParents = React.useMemo(() => {
    if (manageFilter === 'expenses') {
      return parentCategories.filter(cat => (parentExpenseCount.get(cat.id) ?? 0) > 0);
    }
    return parentCategories.filter(cat =>
      cat.transaction_count > 0 ||
      (childrenByParentId.get(cat.id) ?? []).some(c => c.transaction_count > 0)
    );
  }, [manageFilter, parentCategories, parentExpenseCount, childrenByParentId]);

  const handleSetExpenseType = async (category: Category, value: ExpenseType) => {
    await updateCategoryFields.mutateAsync({
      id: category.id,
      fields: {
        description_translated: category.description_translated ?? null,
        parent_id: category.parent_id ?? null,
        parent_description: category.parent_description ?? null,
        expense_type: value,
      },
    });
  };

  const TAB_LABELS: Record<ActiveTab, string> = {
    categories: 'Categorias',
    manage: 'Gerenciamento',
    visualizations: 'Visualizações',
    automations: 'Automações',
  };

  return (
    <div className="space-y-6">
      {/* Sticky header + filtro — bg-gray-50 deve coincidir com o fundo do <main> em Layout.tsx */}
      <div className="sticky top-0 z-10 bg-gray-50 pb-2 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between pt-1">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Categorias</h2>
            <p className="text-gray-600">Organize suas transações por categorias</p>
          </div>
          <div className="flex items-center space-x-3">
            {activeTab === 'categories' && selectedCategories.length >= 1 && (
              <button
                onClick={() => { setBulkDeleteError(''); setIsDeleteBulkModalOpen(true); }}
                className="bg-danger-600 text-white px-4 py-2 rounded-md hover:bg-danger-700 flex items-center space-x-2"
              >
                <Trash2 className="w-4 h-4" />
                <span>Deletar ({selectedCategories.length})</span>
              </button>
            )}
            {activeTab === 'categories' && selectedCategories.length >= 2 && (
              <button
                onClick={handleOpenUnifyModal}
                className="bg-secondary-600 text-white px-4 py-2 rounded-md hover:bg-secondary-700 flex items-center space-x-2"
              >
                <GitMerge className="w-4 h-4" />
                <span>Unificar Categorias ({selectedCategories.length})</span>
              </button>
            )}
            {activeTab === 'categories' && (
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 flex items-center space-x-2"
              >
                <Plus className="w-4 h-4" />
                <span>Nova Categoria</span>
              </button>
            )}
          </div>
        </div>

        {/* Tab navigation */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-6">
            {(Object.keys(TAB_LABELS) as ActiveTab[]).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {TAB_LABELS[tab]}
              </button>
            ))}
          </nav>
        </div>

        {/* Filtro por grupo (only in categories tab) */}
        {activeTab === 'categories' && uniqueParents.length > 0 && (
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-gray-700 whitespace-nowrap">Grupo:</label>
              <select
                value={selectedParent}
                onChange={(e) => {
                  setSelectedParent(e.target.value);
                  setSelectedCategories([]);
                }}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="__all__">Todos os grupos</option>
                {ungroupedCount > 0 && (
                  <option value="__ungrouped__">Sem grupo ({ungroupedCount})</option>
                )}
                {uniqueParents.map(parent => {
                  const cat = catByDescription.get(parent);
                  return (
                    <option key={parent} value={parent}>
                      {cat ? getCategoryLabel(cat) : parent}
                    </option>
                  );
                })}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Categories tab content */}
      {activeTab === 'categories' && isLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      )}
      {activeTab === 'categories' && error && (
        <div className="bg-danger-50 border border-danger-200 rounded-md p-4">
          <p className="text-danger-600">Erro ao carregar categorias</p>
        </div>
      )}
      {activeTab === 'categories' && !isLoading && !error && (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 w-px text-left">
                  <input
                    type="checkbox"
                    checked={selectedCategories.length === displayedCategories.length && displayedCategories.length > 0}
                    onChange={handleSelectAll}
                    className="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nome
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Transações
                </th>
                <th className="px-6 py-3 w-fit relative">
                  <span className="sr-only">Ações</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {displayedCategories.length > 0 ? (
                displayedCategories.map((category) => (
                  <tr key={category.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedCategories.includes(category.description)}
                        onChange={() => handleSelectCategory(category.description)}
                        className="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Tag className="w-5 h-5 text-gray-400 flex-shrink-0" />
                        <span className="text-sm font-medium text-gray-900">
                          {getCategoryLabel(category)}
                        </span>
                        {(() => {
                          // Show inherited expense_type badge
                          const parentCat = categoriesList.find(c => c.id === category.parent_id && c.id !== category.id);
                          const ownType = category.expense_type;
                          const inherited = !ownType && parentCat?.expense_type;
                          const type = ownType || inherited;
                          if (!type) return null;
                          return (
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                              type === 'necessary'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-amber-100 text-amber-700'
                            }`}>
                              {type === 'necessary' ? 'Necessario' : 'Opcional'}
                            </span>
                          );
                        })()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                      {category.transaction_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleEditCategory(category)}
                        className="text-primary-600 hover:text-primary-900 flex items-center space-x-1 ml-auto"
                      >
                        <Edit className="w-4 h-4" />
                        <span>Editar</span>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-gray-500">
                    {selectedParent === '__all__'
                      ? 'Nenhuma categoria encontrada'
                      : selectedParent === '__ungrouped__'
                        ? 'Nenhuma categoria sem grupo'
                        : 'Nenhuma categoria neste grupo'
                    }
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      )}

      {/* Manage tab */}
      {activeTab === 'manage' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between gap-4">
            <p className="text-sm text-gray-500">
              Classifique os grupos de categorias para que a Projeção calcule corretamente gastos necessários e opcionais.
            </p>
            <div className="flex items-center gap-2 flex-shrink-0">
              {(['expenses', 'all'] as const).map(f => (
                <button
                  key={f}
                  onClick={() => setManageFilter(f)}
                  className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                    manageFilter === f
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-500 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {f === 'expenses' ? 'Despesas' : 'Todas'}
                </button>
              ))}
            </div>
          </div>
          {filteredParents.length === 0 ? (
            <p className="px-6 py-12 text-center text-gray-500">Nenhum grupo de categorias encontrado.</p>
          ) : (
            <ul className="divide-y divide-gray-200">
              {filteredParents.map(cat => {
                const children = childrenByParentId.get(cat.id) ?? [];
                return (
                <li key={cat.id} className="px-6 py-4">
                  <div className="flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <span className="text-sm font-medium text-gray-900">
                        {getCategoryLabel(cat)}
                      </span>
                      {children.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {children.map(child => (
                            <span key={child.id} className="text-xs text-gray-400 bg-gray-100 rounded px-1.5 py-0.5">
                              {getCategoryLabel(child)}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    {(
                      [
                        { value: null, label: 'Sem tipo' },
                        { value: 'necessary', label: 'Necessaria' },
                        { value: 'optional', label: 'Opcional' },
                      ] as { value: ExpenseType; label: string }[]
                    ).map(opt => {
                      const active = (cat.expense_type ?? null) === opt.value;
                      return (
                        <button
                          key={String(opt.value)}
                          onClick={() => handleSetExpenseType(cat, opt.value)}
                          disabled={updateCategoryFields.isPending}
                          className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-colors disabled:opacity-50 ${
                            active
                              ? opt.value === 'necessary'
                                ? 'bg-green-100 text-green-700 border-green-300'
                                : opt.value === 'optional'
                                  ? 'bg-amber-100 text-amber-700 border-amber-300'
                                  : 'bg-gray-200 text-gray-700 border-gray-300'
                              : 'bg-white text-gray-400 border-gray-200 hover:bg-gray-50 hover:text-gray-600'
                          }`}
                        >
                          {opt.label}
                        </button>
                      );
                    })}
                  </div>
                  </div>
                </li>
                );
              })}
            </ul>
          )}
        </div>
      )}

      {/* Visualizations tab */}
      {activeTab === 'visualizations' && <VisualizationsSection />}

      {/* Automations tab */}
      {activeTab === 'automations' && <AutomationsTab />}

      {/* Create Category Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Nova Categoria</h3>
                <button
                  onClick={() => setIsCreateModalOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleCreateCategory}>
                <div className="mb-4">
                  <label htmlFor="categoryName" className="block text-sm font-medium text-gray-700 mb-2">
                    Nome da Categoria
                  </label>
                  <input
                    id="categoryName"
                    type="text"
                    value={newCategoryName}
                    onChange={(e) => setNewCategoryName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Digite o nome da categoria"
                    required
                  />
                </div>

                <div className="mb-4">
                  <label htmlFor="newCategoryParent" className="block text-sm font-medium text-gray-700 mb-2">
                    Grupo
                  </label>
                  <select
                    id="newCategoryParent"
                    value={parentSelectValue(newCategoryParentId, newCategoryParentDescription)}
                    onChange={(e) =>
                      handleParentSelectChange(
                        e.target.value,
                        setNewCategoryParentId,
                        setNewCategoryParentDescription,
                        newCategoryName.trim(),
                      )
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    required
                  >
                    <option value="" disabled>Selecione um grupo</option>
                    {uniqueParents.map(parent => {
                      const cat = catByDescription.get(parent);
                      return (
                        <option key={parent} value={cat?.id ?? parent}>
                          {cat ? getCategoryLabel(cat) : parent}
                        </option>
                      );
                    })}
                    <option value="__new__">Criar novo grupo</option>
                  </select>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setIsCreateModalOpen(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={createCategory.isPending || !newCategoryName.trim() || !newCategoryParentId}
                    className="px-4 py-2 bg-primary-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {createCategory.isPending ? 'Criando...' : 'Criar Categoria'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit Category Modal */}
      {isEditModalOpen && editingCategory && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Editar Categoria</h3>
                <button
                  onClick={() => setIsEditModalOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleUpdateCategory}>
                <div className="mb-4">
                  <label htmlFor="editCategoryName" className="block text-sm font-medium text-gray-700 mb-2">
                    Nome da Categoria
                  </label>
                  <input
                    id="editCategoryName"
                    type="text"
                    value={editCategoryName}
                    onChange={(e) => setEditCategoryName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Digite o nome da categoria"
                    required
                  />
                </div>

                <div className="mb-4">
                  <label htmlFor="editDescriptionTranslated" className="block text-sm font-medium text-gray-700 mb-2">
                    Tradução / Apelido
                  </label>
                  <input
                    id="editDescriptionTranslated"
                    type="text"
                    value={editDescriptionTranslated}
                    onChange={(e) => setEditDescriptionTranslated(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Nome traduzido (opcional)"
                  />
                </div>

                <div className="mb-4">
                  <label htmlFor="editParent" className="block text-sm font-medium text-gray-700 mb-2">
                    Grupo
                  </label>
                  <select
                    id="editParent"
                    value={parentSelectValue(editParentId, editParentDescription)}
                    onChange={(e) =>
                      handleParentSelectChange(
                        e.target.value,
                        setEditParentId,
                        setEditParentDescription,
                        editCategoryName.trim(),
                        editingCategory.id,
                      )
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                  >
                    {uniqueParents.map(parent => {
                      const cat = catByDescription.get(parent);
                      return (
                        <option key={parent} value={cat?.id ?? parent}>
                          {cat ? getCategoryLabel(cat) : parent}
                        </option>
                      );
                    })}
                    <option value="__new__">Criar novo grupo</option>
                  </select>
                </div>

                {/* Expense type — only for parent (group) categories */}
                {uniqueParents.includes(editingCategory.description) && (
                  <div className="mb-4">
                    <label htmlFor="editExpenseType" className="block text-sm font-medium text-gray-700 mb-2">
                      Tipo de Gasto
                    </label>
                    <select
                      id="editExpenseType"
                      value={editExpenseType}
                      onChange={(e) => setEditExpenseType(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                    >
                      <option value="">Sem classificacao (opcional por padrao)</option>
                      <option value="necessary">Gasto Necessario</option>
                      <option value="optional">Gasto Opcional</option>
                    </select>
                  </div>
                )}

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setIsEditModalOpen(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={updateCategory.isPending || updateCategoryFields.isPending || !editCategoryName.trim()}
                    className="px-4 py-2 bg-primary-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {(updateCategory.isPending || updateCategoryFields.isPending) ? 'Salvando...' : 'Salvar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Delete Modal */}
      {isDeleteBulkModalOpen && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Confirmar Exclusão</h3>
                <button
                  onClick={() => setIsDeleteBulkModalOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">
                  Tem certeza que deseja deletar {selectedCategories.length === 1 ? 'a categoria' : `as ${selectedCategories.length} categorias`} abaixo?
                </p>
                <ul className="text-sm text-gray-800 list-disc list-inside space-y-1 max-h-40 overflow-y-auto">
                  {selectedCategories.map(name => (
                    <li key={name}>{name}</li>
                  ))}
                </ul>
                <p className="text-xs text-danger-600 mt-2">
                  Categorias em uso por transações não serão deletadas.
                </p>
                {bulkDeleteError && (
                  <pre className="text-xs text-danger-700 bg-danger-50 rounded p-2 mt-2 whitespace-pre-wrap">{bulkDeleteError}</pre>
                )}
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setIsDeleteBulkModalOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleBulkDelete}
                  disabled={deleteCategory.isPending}
                  className="px-4 py-2 bg-danger-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-danger-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {deleteCategory.isPending ? 'Deletando...' : 'Deletar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Unify Categories Modal */}
      {isUnifyModalOpen && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Unificar Categorias</h3>
                <button
                  onClick={() => setIsUnifyModalOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-3">
                  Selecione a categoria de destino para unificação:
                </p>
                <div className="space-y-2">
                  {selectedCategories.map(categoryName => (
                    <label key={categoryName} className="flex items-center">
                      <input
                        type="radio"
                        name="targetCategory"
                        value={categoryName}
                        checked={targetCategory === categoryName}
                        onChange={(e) => setTargetCategory(e.target.value)}
                        className="h-4 w-4 text-primary-600 border-gray-300 focus:ring-primary-500"
                      />
                      <span className="ml-2 text-sm text-gray-900">{categoryName}</span>
                    </label>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-3">
                  Todas as transações das outras categorias selecionadas serão movidas para a categoria de destino.
                </p>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setIsUnifyModalOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleUnifyCategories}
                  disabled={unifyCategories.isPending || !targetCategory}
                  className="px-4 py-2 bg-secondary-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-secondary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {unifyCategories.isPending ? 'Unificando...' : 'Unificar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
