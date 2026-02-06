import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const production = true;
    const productionUrl = '13.48.117.229';
    const baseUrl = `http://${production ? productionUrl : 'localhost'}:8000`;

    // Basic frontend sanitization
    const sanitize = (input) => {
        return input.replace(/<[^>]*>?/gm, '');
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        const sanitizedUser = sanitize(username);

        const formData = new FormData();
        formData.append('username', sanitizedUser);
        formData.append('password', password);

        try {
            const response = await fetch(`${baseUrl}/token`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                if (response.status === 429) {
                    throw new Error('Troppi tentativi. Riprova tra un minuto.');
                } else if (response.status === 401) {
                    throw new Error('Credenziali non valide.');
                } else {
                    throw new Error('Errore durante il login.');
                }
            }

            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            navigate('/');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
            <div className="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden">
                <div className="p-8 text-center bg-indigo-600">
                    <h1 className="text-2xl font-bold text-white">Accedi</h1>
                    <p className="text-indigo-100 mt-2">AI Ambulatorio</p>
                </div>

                <div className="p-8">
                    <form onSubmit={handleLogin} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">Utente</label>
                            <input
                                type="text"
                                required
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full px-4 py-3 rounded-lg bg-slate-50 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors"
                                placeholder="Nome utente"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">Password</label>
                            <input
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-3 rounded-lg bg-slate-50 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors"
                                placeholder="••••••••"
                            />
                        </div>

                        {error && (
                            <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm text-center">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition-all shadow-md hover:shadow-lg"
                        >
                            {loading ? 'Accesso in corso...' : 'Entra'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default Login;
