import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || '/api';

function App() {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTasks = async () => {
    try {
      const res = await fetch(`${API_URL}/tasks`);
      if (!res.ok) throw new Error('Erreur serveur');
      const data = await res.json();
      setTasks(data);
      setError(null);
    } catch (err) {
      setError('Impossible de charger les tâches. Le serveur est-il démarré ?');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTasks(); }, []);

  const addTask = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    try {
      const res = await fetch(`${API_URL}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description }),
      });
      if (!res.ok) throw new Error('Erreur');
      setTitle('');
      setDescription('');
      fetchTasks();
    } catch (err) {
      setError('Erreur lors de l\'ajout');
    }
  };

  const toggleTask = async (task) => {
    await fetch(`${API_URL}/tasks/${task.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ completed: !task.completed }),
    });
    fetchTasks();
  };

  const deleteTask = async (id) => {
    await fetch(`${API_URL}/tasks/${id}`, { method: 'DELETE' });
    fetchTasks();
  };

  return (
    <div className="app">
      <header className="header">
        <h1>📋 Todo App V2</h1>
        <p className="subtitle">Projet DevOps — CI/CD &amp; Kubernetes</p>
      </header>

      <div className="container">
        <div className="add-form">
          <h2>Nouvelle tâche</h2>
          <form onSubmit={addTask}>
            <input
              type="text"
              placeholder="Titre de la tâche"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
            <input
              type="text"
              placeholder="Description (optionnel)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <button type="submit">Ajouter</button>
          </form>
        </div>

        {error && <div className="error">{error}</div>}

        {loading ? (
          <p className="loading">Chargement...</p>
        ) : (
          <div className="task-list">
            <h2>Tâches ({tasks.length})</h2>
            {tasks.length === 0 ? (
              <p className="empty">Aucune tâche pour le moment.</p>
            ) : (
              tasks.map((task) => (
                <div key={task.id} className={`task ${task.completed ? 'completed' : ''}`}>
                  <div className="task-content" onClick={() => toggleTask(task)}>
                    <span className="checkbox">{task.completed ? '✅' : '⬜'}</span>
                    <div>
                      <strong>{task.title}</strong>
                      {task.description && <p>{task.description}</p>}
                    </div>
                  </div>
                  <button className="delete-btn" onClick={() => deleteTask(task.id)}>🗑️</button>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
