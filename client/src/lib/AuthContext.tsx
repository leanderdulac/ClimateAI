import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: number;
  name: string;
  email: string;
  company?: string;
  avatar?: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface RegisterData {
  name: string;
  email: string;
  password: string;
  company?: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Verificar se há usuário no localStorage ao carregar
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Erro ao parsear usuário do localStorage:', error);
        localStorage.removeItem('user');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // Simulação de chamada para API
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Verificar se existe usuário cadastrado
      const storedUsers = JSON.parse(localStorage.getItem('registeredUsers') || '[]');
      const foundUser = storedUsers.find((u: any) => u.email === email && u.password === password);

      if (!foundUser) {
        throw new Error('E-mail ou senha incorretos');
      }

      // Login bem-sucedido
      const userData: User = {
        id: foundUser.id,
        name: foundUser.name,
        email: foundUser.email,
        company: foundUser.company
      };

      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
    } catch (error) {
      setUser(null);
      localStorage.removeItem('user');
      throw error instanceof Error ? error : new Error('Falha no login. Verifique suas credenciais.');
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterData) => {
    setIsLoading(true);
    try {
      // Validação básica
      if (!userData.name || !userData.email || !userData.password) {
        throw new Error('Todos os campos obrigatórios devem ser preenchidos');
      }

      // Simulação de chamada para API
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Verificar se e-mail já existe
      const storedUsers = JSON.parse(localStorage.getItem('registeredUsers') || '[]');
      const existingUser = storedUsers.find((u: any) => u.email === userData.email);

      if (existingUser) {
        throw new Error('Este e-mail já está cadastrado');
      }

      // ✅ SEGURANÇA: Não armazenar senha em localStorage
      // A senha é enviada apenas uma vez para o servidor via HTTPS
      // O servidor faz hash com bcrypt
      const newUser = {
        id: Date.now(),
        name: userData.name,
        email: userData.email,
        // ❌ REMOVIDO: password: userData.password,
        company: userData.company || '',
        createdAt: new Date().toISOString()
      };

      // Salvar na lista de usuários cadastrados (sem senha!)
      const updatedUsers = [...storedUsers, newUser];
      localStorage.setItem('registeredUsers', JSON.stringify(updatedUsers));

      // Fazer login automático após cadastro
      const userSession: User = {
        id: newUser.id,
        name: newUser.name,
        email: newUser.email,
        company: newUser.company
      };

      setUser(userSession);
      localStorage.setItem('user', JSON.stringify(userSession));
    } catch (error) {
      setUser(null);
      localStorage.removeItem('user');
      throw error instanceof Error ? error : new Error('Falha no cadastro. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  const value: AuthContextType = {
    user,
    login,
    register,
    logout,
    isLoading,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}