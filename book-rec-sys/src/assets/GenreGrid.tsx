type GenreGridProps = {
    genres: string[];
    onGenreClick: (genre: string) => void;
};

const GenreGrid: React.FC<GenreGridProps> = ({ genres, onGenreClick }) => {
    return (
        <div className="genre-grid">
            {genres.map((genre) => (
                <button
                    key={genre}
                    className="genre-button"
                    onClick={() => onGenreClick(genre)}
                >
                    {genre}
                </button>
            ))}
        </div>
    );
};

export default GenreGrid;
