import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SearchPage from './components/SearchPage';
import UserDetail from './components/UserDetail';
import './styles/main.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/user/:email" element={<UserDetail />} />
      </Routes>
    </Router>
  );
}

export default App;
