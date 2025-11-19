import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "@/lib/AuthContext";
import {
  Globe,
  Home,
  Coins,
  BarChart3,
  Menu,
  X,
  ChevronDown,
  Settings,
  User,
  LogOut,
  UserCircle
} from "lucide-react";

interface NavigationItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
}

const navigationItems: NavigationItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: Home,
    description: "Visão geral e analytics"
  },
  {
    label: "Tokenização",
    href: "/tokenization",
    icon: Coins,
    description: "Criar e gerenciar tokens"
  },
  {
    label: "Analytics",
    href: "/analytics",
    icon: BarChart3,
    description: "Análises avançadas"
  }
];

export function NavigationMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const { user, logout } = useAuth();

  const isActive = (href: string) => {
    if (href === "/dashboard" && location.pathname === "/") return true;
    return location.pathname === href;
  };

  const handleLogout = () => {
    logout();
    setIsOpen(false);
  };

  return (
    <div className="relative">
      {/* Desktop Navigation */}
      <div className="hidden md:flex items-center gap-6">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              to={item.href}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-200 ${isActive(item.href)
                  ? "bg-blue-100 text-blue-700 font-medium"
                  : "text-gray-600 hover:text-blue-600 hover:bg-gray-50"
                }`}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </div>

      {/* Mobile Navigation Button */}
      <div className="md:hidden">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2"
        >
          <Menu className="h-4 w-4" />
          Menu
          <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </Button>
      </div>

      {/* Mobile Dropdown Menu */}
      {isOpen && (
        <Card className="absolute top-full right-0 mt-2 w-80 z-50 shadow-xl border-0 md:hidden">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Navegação</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsOpen(false)}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="space-y-2">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    onClick={() => setIsOpen(false)}
                    className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-200 ${isActive(item.href)
                        ? "bg-blue-50 text-blue-700 border border-blue-200"
                        : "text-gray-700 hover:bg-gray-50 hover:text-blue-600"
                      }`}
                  >
                    <div className={`p-2 rounded-lg ${isActive(item.href) ? "bg-blue-100" : "bg-gray-100"
                      }`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="font-medium">{item.label}</div>
                      {item.description && (
                        <div className="text-sm text-gray-500">{item.description}</div>
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>

            <div className="border-t border-gray-200 mt-4 pt-4">
              {user && (
                <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <UserCircle className="h-8 w-8 text-gray-600" />
                    <div>
                      <p className="font-medium text-sm">{user.name}</p>
                      <p className="text-xs text-gray-500">{user.email}</p>
                      {user.company && (
                        <p className="text-xs text-gray-500">{user.company}</p>
                      )}
                    </div>
                  </div>
                </div>
              )}
              <div className="space-y-2">
                <Button variant="ghost" className="w-full justify-start gap-3">
                  <User className="h-4 w-4" />
                  Perfil
                </Button>
                <Button variant="ghost" className="w-full justify-start gap-3">
                  <Settings className="h-4 w-4" />
                  Configurações
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-3 text-red-600 hover:text-red-700 hover:bg-red-50"
                  onClick={handleLogout}
                >
                  <LogOut className="h-4 w-4" />
                  Sair
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
