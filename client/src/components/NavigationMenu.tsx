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
  FlaskConical as Lab,
  LogOut
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
    description: "Portfolio & Riscos"
  },
  {
    label: "Lab Atuarial",
    href: "/actuarial-lab",
    icon: Lab,
    description: "Design & Backtesting"
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
      <div className="hidden md:flex items-center gap-1">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const isItemActive = isActive(item.href);
          return (
            <Link
              key={item.href}
              to={item.href}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all duration-200 text-sm font-medium ${isItemActive
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                }`}
            >
              <Icon className={`h-4 w-4 ${isItemActive ? "text-primary" : "text-muted-foreground"}`} />
              {item.label}
            </Link>
          );
        })}
      </div>

      {/* Mobile Navigation Button */}
      <div className="md:hidden">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsOpen(!isOpen)}
          className="relative text-muted-foreground hover:text-foreground"
        >
          <Menu className="h-5 w-5" />
        </Button>
      </div>

      {/* Mobile Dropdown Menu */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 md:hidden"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full right-0 mt-2 w-full min-w-[300px] z-50 md:hidden p-4">
            <Card className="border-border shadow-lg overflow-hidden animate-in fade-in zoom-in-95 duration-200">
              <div className="p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-foreground">Menu</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setIsOpen(false)}
                    className="h-8 w-8"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                <div className="space-y-1">
                  {navigationItems.map((item) => {
                    const Icon = item.icon;
                    const isItemActive = isActive(item.href);
                    return (
                      <Link
                        key={item.href}
                        to={item.href}
                        onClick={() => setIsOpen(false)}
                        className={`flex items-start gap-3 p-3 rounded-lg transition-colors ${isItemActive
                          ? "bg-primary/5 text-primary"
                          : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                          }`}
                      >
                        <Icon className={`h-5 w-5 mt-0.5 ${isItemActive ? "text-primary" : "text-muted-foreground"}`} />
                        <div>
                          <div className="font-medium text-sm">{item.label}</div>
                          {item.description && (
                            <div className="text-xs text-muted-foreground/80 mt-0.5">{item.description}</div>
                          )}
                        </div>
                      </Link>
                    );
                  })}
                </div>

                <div className="border-t border-border mt-4 pt-4">
                  {user && (
                    <div className="mb-4 p-3 bg-muted/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        {/* UserCircle removed: unused icon */}
                        <div>
                          <p className="font-medium text-sm text-foreground">{user.name}</p>
                          <p className="text-xs text-muted-foreground">{user.email}</p>
                          {user.company && (
                            <p className="text-xs text-muted-foreground">{user.company}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                  <div className="space-y-2">
                    <Button variant="ghost" className="w-full justify-start gap-3 hover:bg-muted/50">
                      <User className="h-4 w-4" />
                      Perfil
                    </Button>
                    <Button variant="ghost" className="w-full justify-start gap-3 hover:bg-muted/50">
                      <Settings className="h-4 w-4" />
                      Configurações
                    </Button>
                    <Button
                      variant="ghost"
                      className="w-full justify-start gap-3 text-destructive hover:text-destructive hover:bg-destructive/10"
                      onClick={handleLogout}
                    >
                      <LogOut className="h-4 w-4" />
                      Sair
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
