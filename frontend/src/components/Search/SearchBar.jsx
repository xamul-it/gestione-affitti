import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchAPI } from '../../services/api';
import {
  Loader2, Search, User, Building, Building2, FileText,
  Users, CalendarCheck, Puzzle, Home, X, ChevronRight
} from 'lucide-react';
import './SearchBar.css';

// Icon mapping for entity types
const ENTITY_ICONS = {
  'user': User,
  'building': Building,
  'building-2': Building2,
  'home': Home,
  'file-text': FileText,
  'users': Users,
  'calendar-check': CalendarCheck,
  'puzzle': Puzzle,
};

// Get icon component for entity
function getEntityIcon(iconName) {
  return ENTITY_ICONS[iconName] || Search;
}

function SearchBar() {
  const [query, setQuery] = useState('');
  const [groupedResults, setGroupedResults] = useState({});
  const [flatResults, setFlatResults] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [activeFilter, setActiveFilter] = useState(null);
  const searchRef = useRef(null);
  const inputRef = useRef(null);
  const abortControllerRef = useRef(null);
  const navigate = useNavigate();

  // Debounced search with abort controller to prevent race conditions
  useEffect(() => {
    setError(null);

    if (query.length < 2) {
      setGroupedResults({});
      setFlatResults([]);
      setTotalCount(0);
      setIsOpen(false);
      setError(null);
      return;
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    const timeoutId = setTimeout(async () => {
      try {
        setLoading(true);
        setError(null);

        // Use unified search endpoint
        const response = await searchAPI.searchUnified(query, {
          limit_per_entity: 5,
          limit: 25,
          modules: activeFilter ? activeFilter : undefined,
        });

        if (!signal.aborted) {
          const data = response.data;
          setGroupedResults(data.results || {});
          setTotalCount(data.total || 0);

          // Create flat list for keyboard navigation
          const flat = [];
          Object.entries(data.results || {}).forEach(([key, entityData]) => {
            entityData.items.forEach(item => {
              flat.push({
                ...item,
                entityKey: key,
                entityInfo: entityData,
              });
            });
          });
          setFlatResults(flat);

          setIsOpen(data.total > 0 || query.length >= 2);
        }
      } catch (err) {
        if (err.name === 'AbortError' || signal.aborted) {
          return;
        }

        console.error('Errore ricerca:', err);

        let errorMessage = 'Errore durante la ricerca.';

        if (!navigator.onLine) {
          errorMessage = 'Connessione assente. Verifica la rete.';
        } else if (err.response) {
          if (err.response.status >= 500) {
            errorMessage = 'Errore del server. Riprova più tardi.';
          } else if (err.response.status === 404) {
            errorMessage = 'Servizio di ricerca non disponibile.';
          } else if (err.response.status === 429) {
            errorMessage = 'Troppe richieste. Attendi un momento.';
          }
        } else if (err.request) {
          errorMessage = 'Nessuna risposta dal server.';
        }

        setError(errorMessage);
        setGroupedResults({});
        setFlatResults([]);
        setTotalCount(0);
        setIsOpen(true);
      } finally {
        if (!signal.aborted) {
          setLoading(false);
        }
      }
    }, 300);

    return () => {
      clearTimeout(timeoutId);
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [query, activeFilter]);

  // Close on click outside
  const handleClickOutside = useCallback((event) => {
    if (searchRef.current && !searchRef.current.contains(event.target)) {
      setIsOpen(false);
      setSelectedIndex(-1);
      setError(null);
    }
  }, []);

  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [handleClickOutside]);

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (!isOpen || flatResults.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev =>
          prev < flatResults.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && flatResults[selectedIndex]) {
          handleResultClick(flatResults[selectedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setSelectedIndex(-1);
        inputRef.current?.blur();
        break;
      default:
        break;
    }
  };

  const handleResultClick = (result) => {
    navigate(result.url);
    setIsOpen(false);
    setQuery('');
    setSelectedIndex(-1);
    setActiveFilter(null);
  };

  const clearSearch = () => {
    setQuery('');
    setGroupedResults({});
    setFlatResults([]);
    setTotalCount(0);
    setIsOpen(false);
    setActiveFilter(null);
    inputRef.current?.focus();
  };

  const handleFilterClick = (moduleName) => {
    setActiveFilter(activeFilter === moduleName ? null : moduleName);
    setSelectedIndex(-1);
  };

  // Get unique modules from results for filter chips
  const availableModules = Object.values(groupedResults).reduce((acc, entity) => {
    if (!acc.find(m => m.name === entity.module_name)) {
      acc.push({
        name: entity.module_name,
        displayName: entity.display_name_plural,
        color: entity.color,
        icon: entity.icon,
      });
    }
    return acc;
  }, []);

  // Calculate flat index for a result within grouped display
  let currentFlatIndex = -1;

  return (
    <div className="search-bar" ref={searchRef}>
      <div className="search-input-wrapper">
        <span className="search-icon" aria-hidden="true">
          <Search size={18} />
        </span>
        <input
          ref={inputRef}
          type="text"
          className="search-input"
          placeholder="Cerca in tutto il sistema..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (totalCount > 0 || query.length >= 2) setIsOpen(true);
          }}
        />
        {loading && (
          <span className="search-loading" aria-hidden="true">
            <Loader2 size={16} className="spinning" />
          </span>
        )}
        {query && !loading && (
          <button
            className="search-clear"
            onClick={clearSearch}
            type="button"
            aria-label="Cancella ricerca"
          >
            <X size={16} />
          </button>
        )}
      </div>

      {isOpen && (
        <div className="search-results-container">
          {/* Filter chips when we have results */}
          {availableModules.length > 1 && (
            <div className="search-filters">
              <span className="filters-label">Filtra:</span>
              {availableModules.map(module => (
                <button
                  key={module.name}
                  className={`filter-chip ${activeFilter === module.name ? 'active' : ''}`}
                  onClick={() => handleFilterClick(module.name)}
                  style={{
                    '--chip-color': module.color,
                  }}
                >
                  {module.displayName}
                </button>
              ))}
            </div>
          )}

          {/* Grouped results */}
          {totalCount > 0 && (
            <div className="search-results-grouped">
              {Object.entries(groupedResults).map(([entityKey, entityData]) => {
                // Filter by active module
                if (activeFilter && entityData.module_name !== activeFilter) {
                  return null;
                }

                const IconComponent = getEntityIcon(entityData.icon);

                return (
                  <div key={entityKey} className="result-group">
                    <div
                      className="result-group-header"
                      style={{ '--group-color': entityData.color }}
                    >
                      <IconComponent size={14} />
                      <span className="group-title">{entityData.display_name_plural}</span>
                      <span className="group-count">{entityData.count}</span>
                    </div>
                    <div className="result-group-items">
                      {entityData.items.map((result) => {
                        currentFlatIndex++;
                        const isSelected = currentFlatIndex === selectedIndex;

                        return (
                          <div
                            key={`${entityKey}-${result.id}`}
                            className={`search-result-item ${isSelected ? 'selected' : ''}`}
                            onClick={() => handleResultClick(result)}
                            onMouseEnter={() => setSelectedIndex(currentFlatIndex)}
                          >
                            <div className="result-content">
                              <div className="result-title">{result.title}</div>
                              {result.subtitle && (
                                <div className="result-subtitle">{result.subtitle}</div>
                              )}
                            </div>
                            <ChevronRight size={14} className="result-arrow" />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Total count footer */}
          {totalCount > 0 && (
            <div className="search-results-footer">
              <span>{totalCount} risultat{totalCount === 1 ? 'o' : 'i'} trovati</span>
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="search-error">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {/* No results */}
          {!error && query.length >= 2 && totalCount === 0 && !loading && (
            <div className="search-no-results">
              <Search size={24} className="no-results-icon" />
              <p>Nessun risultato per "{query}"</p>
              <span className="no-results-hint">Prova con termini diversi o meno specifici</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SearchBar;
