// Script simples para testar o fluxo de autenticação
console.log("=== Teste do Sistema de Autenticação ===");

// Simular cadastro
const testUser = {
  id: Date.now(),
  name: "João Silva",
  email: "joao@teste.com",
  password: "senha123",
  company: "Empresa Teste"
};

// Salvar usuário cadastrado
const storedUsers = JSON.parse(localStorage.getItem("registeredUsers") || "[]");
storedUsers.push(testUser);
localStorage.setItem("registeredUsers", JSON.stringify(storedUsers));

console.log("✅ Usuário cadastrado:", testUser);

// Simular login
const loginCredentials = {
  email: "joao@teste.com",
  password: "senha123"
};

const registeredUsers = JSON.parse(localStorage.getItem("registeredUsers") || "[]");
const foundUser = registeredUsers.find(u => u.email === loginCredentials.email && u.password === loginCredentials.password);

if (foundUser) {
  console.log("✅ Login bem-sucedido para:", foundUser.name);
  localStorage.setItem("user", JSON.stringify({
    id: foundUser.id,
    name: foundUser.name,
    email: foundUser.email,
    company: foundUser.company
  }));
} else {
  console.log("❌ Credenciais inválidas");
}

console.log("=== Fim do Teste ===");
