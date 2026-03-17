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

    window.open(`http://localhost:8000/api/circular/api/reports/download-pdf/?${params.toString()}`, '_blank');
  };

  return (
    <div className="min-h-[10vh] bg-gradient-to-b from-sky-50 to-white text-slate-800">
      {/* 🔝 Top Bar — now inside FilterBar */}
      <div className="sticky top-0 z-30 border-b border-sky-100 bg-white/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        
        
        </div>
      </div>

      {/* 📋 Actual Filter Controls */}
      <div className="border-b border-sky-100 bg-white/70">
        <div className="max-w-7xl mx-auto px-4 py-3 grid gap-3 lg:grid-cols-12">
          {canUseSearch && (
            <div className="lg:col-span-5 relative">
              <LuSearch className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search titles, tags..."
                value={searchTerm}
                onChange={(e) => onSearchChange(e.target.value)}
                className="pl-9 w-full px-3 py-1.5 border border-slate-300 rounded-md bg-white"
              />
            </div>
          )}

          <div className="lg:col-span-7 flex flex-wrap items-center gap-2">
            {canUseDeptFilter && (
              <>
                <div className="flex items-center gap-2">
                  {deptTypes.map(dept => (
                    <button
                      key={dept}
                      onClick={() => onToggleScope(dept)}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium border ${
                        scope.includes(dept)
                          ? 'bg-sky-600 text-white border-sky-600'
                          : 'bg-white text-slate-700 border-sky-200 hover:bg-sky-50'
                      }`}
                    >
                      {dept}
                    </button>
                  ))}
                </div>
                <div className="h-6 w-px bg-sky-200 hidden md:block" />
              </>
            )}

            {canUseTypeFilter && (
              <>
                <div className="flex items-center gap-2">
                  {notificationTypes.map(type => (
                    <button
                      key={type}
                      onClick={() => onToggleType(type)}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium border ${
                        selectedTypes.includes(type)
                          ? 'bg-sky-600 text-white border-sky-600'
                          : 'bg-white text-slate-700 border-sky-200 hover:bg-sky-50'
                      }`}
                    >
                      {type}
                    </button>
                  ))}
                </div>
                <div className="h-6 w-px bg-sky-200 hidden md:block" />
              </>
            )}

            {canUseCriticalityFilter && (
              <div className="flex items-center gap-2">
                {criticalities.map(crit => (
                  <button
                    key={crit}
                    onClick={() => onToggleCriticality(crit)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border ${
                      selectedCriticalities.includes(crit)
                        ? 'bg-sky-600 text-white border-sky-600'
                        : 'bg-white text-slate-700 border-sky-200 hover:bg-sky-50'
                    }`}
                  >
                    {crit}
                  </button>
                ))}
              </div>
            )}

            {canUseUnreadToggle && (
              <div className="ml-auto flex items-center gap-2">
                <label className="flex items-center gap-2 text-xs text-slate-600">
                  <input
                    type="checkbox"
                    checked={onlyUnread}
                    onChange={(e) => onToggleOnlyUnread(e.target.checked)}
                    className="sr-only"
                  />
                  <span>Only unread</span>
                  <div className={`w-12 h-6 rounded-full relative ${onlyUnread ? 'bg-sky-500' : 'bg-gray-300'}`}>
                    <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform ${onlyUnread ? 'translate-x-6' : 'translate-x-0.5'}`}></div>
                  </div>
                </label>
              </div>
            )}
            {/* 👇 PDF Download Button */}
              {canUseDownload && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 px-2 bg-green-600 hover:bg-green-700 text-white flex items-center gap-1"
                  onClick={handleDownload}
                >
                  <Download className="h-3 w-3" />
                  <span className="text-xs">Download</span>
                </Button>
              )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilterBar;