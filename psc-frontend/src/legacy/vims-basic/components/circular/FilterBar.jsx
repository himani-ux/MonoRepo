// src/components/FilterBar.jsx
import React from 'react';
import { LuSearch } from 'react-icons/lu';
import { Button } from "./ui/button";
import { Download } from "lucide-react";

const FilterBar = ({
  user,
  searchTerm,
  onSearchChange, 
  scope,
  onToggleScope,
  selectedTypes,
  onToggleType,
  selectedCriticalities,
  onToggleCriticality,
  onlyUnread,
  onToggleOnlyUnread,
  canUseSearch = true,
  canUseDeptFilter = true,
  canUseTypeFilter = true,
  canUseCriticalityFilter = true,
  canUseUnreadToggle = true,
  canUseDownload = true,
}) => {
  const deptTypes = ["SEQ", "Technical"];
  const notificationTypes = ["Alert", "Circular", "Work Instruction"];
  const criticalities = ["Critical", "High", "Medium", "Low"];

  const handleDownload = () => {
    if (!user?.crew_id) {
      alert('Please log in again.');
      return;
    }

    const params = new URLSearchParams({
      crew_id: user.crew_id,
      types: selectedTypes.join(','),
      criticalities: selectedCriticalities.join(','),
      scope: scope.join(','),
      search: searchTerm,
      only_unread: onlyUnread.toString(),
    });

    window.open(`http://localhost:8001/api/circular/api/reports/download-pdf/?${params.toString()}`, '_blank');
  };

  return (
    <div className="mb-6 rounded-lg border border-neutral-200 bg-white shadow-md">
      <div className="grid gap-4 p-4 lg:grid-cols-12 lg:items-start">
          {canUseSearch && (
            <div className="lg:col-span-4">
              <div className="relative flex h-10 items-center">
                <LuSearch className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
                <input
                  type="text"
                  placeholder="Search titles, tags..."
                  value={searchTerm}
                  onChange={(e) => onSearchChange(e.target.value)}
                  className="h-10 w-full rounded-md border border-neutral-300 bg-white pl-10 pr-3 text-sm text-neutral-800 placeholder:text-neutral-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                />
              </div>
            </div>
          )}

          <div className={`${canUseDownload ? 'lg:col-span-6' : canUseSearch ? 'lg:col-span-8' : 'lg:col-span-12'} flex flex-wrap items-center gap-2`}>
            {canUseDeptFilter && (
              <>
                <div className="flex items-center gap-2">
                  {deptTypes.map(dept => (
                    <button
                      key={dept}
                      onClick={() => onToggleScope(dept)}
                      className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                        scope.includes(dept)
                          ? 'border-primary-200 bg-primary-50 text-primary-700'
                          : 'border-neutral-300 bg-white text-neutral-700 hover:bg-neutral-50'
                      }`}
                    >
                      {dept}
                    </button>
                  ))}
                </div>
                <div className="hidden h-6 w-px bg-neutral-200 md:block" />
              </>
            )}

            {canUseTypeFilter && (
              <>
                <div className="flex items-center gap-2">
                  {notificationTypes.map(type => (
                    <button
                      key={type}
                      onClick={() => onToggleType(type)}
                      className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                        selectedTypes.includes(type)
                          ? 'border-primary-200 bg-primary-50 text-primary-700'
                          : 'border-neutral-300 bg-white text-neutral-700 hover:bg-neutral-50'
                      }`}
                    >
                      {type}
                    </button>
                  ))}
                </div>
                <div className="hidden h-6 w-px bg-neutral-200 md:block" />
              </>
            )}

            {canUseCriticalityFilter && (
              <div className="flex items-center gap-2">
                {criticalities.map(crit => (
                  <button
                    key={crit}
                    onClick={() => onToggleCriticality(crit)}
                    className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                      selectedCriticalities.includes(crit)
                        ? 'border-primary-200 bg-primary-50 text-primary-700'
                        : 'border-neutral-300 bg-white text-neutral-700 hover:bg-neutral-50'
                    }`}
                  >
                    {crit}
                  </button>
                ))}
              </div>
            )}

            {canUseUnreadToggle && (
              <div className="ml-auto flex items-center gap-2">
                <label className="flex items-center gap-2 text-xs text-neutral-600">
                  <input
                    type="checkbox"
                    checked={onlyUnread}
                    onChange={(e) => onToggleOnlyUnread(e.target.checked)}
                    className="sr-only"
                  />
                  <span>Only unread</span>
                  <div className={`relative h-6 w-12 rounded-full transition-colors ${onlyUnread ? 'bg-primary-500' : 'bg-neutral-300'}`}>
                    <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform ${onlyUnread ? 'translate-x-6' : 'translate-x-0.5'}`}></div>
                  </div>
                </label>
              </div>
            )}
          </div>
          {canUseDownload && (
            <div className={`${canUseSearch ? 'lg:col-span-2' : 'lg:col-span-12'} flex justify-start lg:justify-end`}>
              <Button
                size="sm"
                className="h-10 gap-2 bg-success-600 px-4 text-white hover:bg-success-700"
                onClick={handleDownload}
              >
                <Download className="h-4 w-4" />
                <span className="text-sm">Download</span>
              </Button>
            </div>
          )}
      </div>
    </div>
  );
};

export default FilterBar;
