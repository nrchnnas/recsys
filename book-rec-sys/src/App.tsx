import './App.css';
import Title, { Panel, GenreSection} from './Home';

function Web() {
  return (
    <div>
        <Title />

        <div className="two-column-container">
          <div>
            <GenreSection />
          </div>

          <div>
            <Panel />
          </div>
      </div>
      
    </div>
);
}

export default Web;