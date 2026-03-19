
import { useState, useEffect, useRef } from "react";
import { Button } from "./OrbUI";

const ReportFilter = ({
  onFilterSelect,
  isVisible,
  onClose,
  canAccessFilterReports,
}) => {
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const wrapperRef = useRef(null);

  const filterOptions = [
    { key: "TM", label: "This Month" },
    { key: "1M", label: "Last Month" },
    { key: "6M", label: "Last 6 Months" },
    { key: "1Y", label: "Last Year" },
    { key: "3Y", label: "Last 3 Years" },
  ];

  // ✅ Correct outside click handling
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target)
      ) {
        setIsFilterOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () =>
      document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleFilterClick = (filterKey) => {
    onFilterSelect(filterKey);
    setIsFilterOpen(false);
  };

  return (
    <div
      ref={wrapperRef}
      className="orb-report-filter"
    >
      {canAccessFilterReports && (
        <Button onClick={() => setIsFilterOpen((prev) => !prev)}>
          Filter Report
        </Button>
      )}

      {isFilterOpen && (
        <div className="filter-dropdown">
          {filterOptions.map((option) => (
            <div
              key={option.key}
              onClick={() => handleFilterClick(option.key)}
              className="filter-dropdown-item"
            >
              {option.label}
            </div>
          ))}
        </div>
      )}

      {isVisible && (
        <Button variant="secondary" onClick={onClose}>
          Close Report
        </Button>
      )}
    </div>
  );
};

export default ReportFilter;
