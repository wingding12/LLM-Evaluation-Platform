import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import HomePage from "./pages/HomePage";
import ExperimentPage from "./pages/ExperimentPage";
import TestCasePage from "./pages/TestCasePage";
import "./styles/global.css";

const App: React.FC = () => {
  return (
    <Router>
      <div className="container">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/experiment" element={<ExperimentPage />} />
          <Route path="/test-cases" element={<TestCasePage />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
