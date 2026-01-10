import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchAPI } from '../../services/api';
import { Loader2, Search } from 'lucide-react';
import './SearchBar.css';

function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchRef = useRef(null);
  const abortControllerRef = useRef(null);
  const navigate = useNavigate();

  // Debounced search with abort controller to prevent race conditions
  useEffect(() => {
    // Reset error on new query
    setError(null);

    if (query.length < 2) {
      setResults([]);
      setIsOpen(false);
      setError(null);
      return;
    }

    // Abort previous request if exists
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    const timeoutId = setTimeout(async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await searchAPI.search(query);

        // Only update state if request wasn't aborted
        if (!signal.aborted) {
          setResults(response.data.results);
          setIsOpen(response.data.results.length > 0);
        }
      } catch (err) {
        // Don't show error if request was aborted (user is still typing)
        if (err.name === 'AbortError' || signal.aborted) {
          return;
        }

        console.error('Errore ricerca:', err);

        // User-friendly error messages
        let errorMessage = 'Errore durante la ricerca.';

        if (!navigator.onLine) {
          errorMessage = 'Connessione assente. Verifica la rete.';
        } else if (err.response) {
          // Server responded with error status
          if (err.response.status >= 500) {
            errorMessage = 'Errore del server. Riprova più tardi.';
          } else if (err.response.status === 404) {
            errorMessage = 'Servizio di ricerca non disponibile.';
          } else if (err.response.status === 429) {
            errorMessage = 'Troppe richieste. Attendi un momento.';
          }
        } else if (err.request) {
          // Request made but no response received
          errorMessage = 'Nessuna risposta dal server.';
        }

        setError(errorMessage);
        setResults([]);
        setIsOpen(true); // Show error dropdown
      } finally {
        if (!signal.aborted) {
          setLoading(false);
        }
      }
    }, 300);

    // Cleanup function
    return () => {
      clearTimeout(timeoutId);
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [query]);

  // Close on click outside - use useCallback to prevent memory leak
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
    if (!isOpen || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev =>
          prev < results.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && results[selectedIndex]) {
          handleResultClick(results[selectedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setSelectedIndex(-1);
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
  };

  const getTypeEmoji = (type) => {
    switch (type) {
      case 'immobile':
        return '🏢';
      case 'affittuario':
        return '👤';
      case 'contratto':
        return '📄';
      default:
        return '📋';
    }
  };

  const getTypeLabel = (type) => {
    switch (type) {
      case 'immobile':
        return 'Immobile';
      case 'affittuario':
        return 'Affittuario';
      case 'contratto':
        return 'Contratto';
      default:
        return type;
    }
  };

  return (
    <div className="search-bar" ref={searchRef}>
      <div className="search-input-wrapper">
        <span className="search-icon" aria-hidden="true">
          <Search size={18} />
        </span>
        <input
          type="text"
          className="search-input"
          placeholder="Cerca immobile, affittuario, contratto..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (results.length > 0) setIsOpen(true);
          }}
        />
        {loading && (
          <span className="search-loading" aria-hidden="true">
            <Loader2 size={16} />
          </span>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div className="search-results">
          {results.map((result, index) => (
            <div
              key={`${result.type}-${result.id}`}
              className={`search-result-item ${
                index === selectedIndex ? 'selected' : ''
              }`}
              onClick={() => handleResultClick(result)}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <div className="result-icon">
                {getTypeEmoji(result.type)}
              </div>
              <div className="result-content">
                <div className="result-title">{result.title}</div>
                <div className="result-subtitle">{result.subtitle}</div>
              </div>
              <div className="result-type-badge">
                {getTypeLabel(result.type)}
              </div>
            </div>
          ))}
        </div>
      )}

      {isOpen && error && (
        <div className="search-results">
          <div className="search-error">
            <span className="error-icon">⚠️</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {isOpen && !error && query.length >= 2 && results.length === 0 && !loading && (
        <div className="search-results">
          <div className="search-no-results">
            Nessun risultato trovato per "{query}"
          </div>
        </div>
      )}
    </div>
  );
}

export default SearchBar;
