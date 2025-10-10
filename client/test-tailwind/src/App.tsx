import React from 'react';
import './App.css';

function App() {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-lg">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-4">
          Tailwind CSS Test
        </h1>
        <p className="text-gray-600 text-center mb-6">
          If you can see this styled correctly, Tailwind CSS is working!
        </p>
        <div className="flex justify-center space-x-4">
          <button className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded">
            Primary
          </button>
          <button className="bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded">
            Secondary
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
