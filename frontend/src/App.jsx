import { useState, useEffect } from 'react';
import Home from './components/Home';
import Play from './components/Play';
import StoryList from './components/StoryList';
import StoryDetail from './components/StoryDetail';
import { initAudio } from './audio';
import './index.css';

function App() {
  const [view, setView] = useState('home');
  const [currentStory, setCurrentStory] = useState(null);
  const [playKey, setPlayKey] = useState(0);

  useEffect(() => {
    initAudio();
  }, []);

  const handleSetView = (newView) => {
    if (newView === 'play_restart') {
        setPlayKey(k => k + 1);
        setView('play');
    } else {
        setView(newView);
    }
  };

  return (
    <>
      <audio id="snd-click" src="/click.mp3" preload="auto"></audio>
      <audio id="snd-bgm" loop src="/bgm.mp3" preload="auto"></audio>
      
      <div style={{position: 'fixed', bottom: 0, left: 0, color: 'white', fontSize: '1rem', zIndex: 100, pointerEvents: 'none'}}>Minecraft v1.0.0</div>

      {view === 'home' && <Home setView={handleSetView} />}
      {view === 'play' && <Play key={playKey} setView={handleSetView} />}
      {view === 'list' && <StoryList setView={handleSetView} setCurrentStory={setCurrentStory} />}
      {view === 'detail' && <StoryDetail setView={handleSetView} story={currentStory} />}
    </>
  );
}

export default App;
