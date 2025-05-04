import { useState } from 'react';
import { IoSearch } from "react-icons/io5";

interface SearchBarProps {
  onSearch: (query: string) => void;
}

const SearchBar = ({ onSearch }: SearchBarProps) => {
  const [searchQuery, setSearchQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      onSearch(searchQuery.trim());
    }
  };

  return (
    <form 
      onSubmit={handleSubmit} 
      className="search-bar"
    >
      <div className="search-input-container">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search for books..."
          className="search-input"
        />
        <button type="submit" className="search-button">
          <IoSearch />
        </button>
      </div>
    </form>
  );
};

export default SearchBar;