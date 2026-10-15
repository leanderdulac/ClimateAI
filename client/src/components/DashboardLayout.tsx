import { ReactNode, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { NavigationMenu } from "@/components/NavigationMenu";
import { useAuth } from "@/lib/AuthContext";
import { LogOut } from "lucide-react";
import { Link } from "react-router-dom";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { useTranslation } from "@/hooks/useTranslation";
import { Logo } from "@/components/Logo";

interface DashboardLayoutProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
}

export function DashboardLayout({ children, title, subtitle }: DashboardLayoutProps) {
  const { user, logout } = useAuth();
  const { t } = useTranslation();

  useEffect(() => {
    const root = document.documentElement;
    root.classList.add('command-center');
    return () => root.classList.remove('command-center');
  }, []);

  return (
    <div className="command-center min-h-screen bg-background text-foreground font-sans">
      <nav className="sticky top-0 z-50 w-full border-b border-border/40 bg-[#0F172A]/80 backdrop-blur-md supports-[backdrop-filter]:bg-[#0F172A]/70">
        <div className="mx-auto w-full max-w-[96rem] px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3 md:gap-8">
              <Link to="/" className="flex shrink-0 items-center transition-opacity hover:opacity-80">
                <Logo size={32} />
              </Link>
              <div className="shrink-0">
                <NavigationMenu />
              </div>
            </div>

            <div className="flex shrink-0 items-center gap-1 sm:gap-4">
              <LanguageSwitcher />
              <div className="h-6 w-px bg-border/60 hidden sm:block" />

              {user ? (
                <div className="flex items-center gap-3">
                  <div className="hidden md:block text-right">
                    <div className="text-sm font-medium text-foreground leading-none">{user.name}</div>
                    <div className="text-xs text-muted-foreground mt-1">{user.email}</div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={logout}
                    className="text-muted-foreground hover:text-destructive transition-colors"
                  >
                    <Link to="/logout" onClick={(e) => { e.preventDefault(); logout(); }}>
                      <LogOut className="h-5 w-5" />
                    </Link>
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Link to="/auth?tab=login">
                    <Button variant="ghost" size="sm" className="hidden sm:flex">
                      {t('nav.login')}
                    </Button>
                  </Link>
                  <Link to="/auth?tab=register">
                    <Button size="sm" className="bg-primary hover:bg-primary/90 text-primary-foreground font-medium shadow-sm">
                      {t('nav.signup')}
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {title && (
        <header className="border-b border-border/40 bg-card/30 backdrop-blur-sm">
          <div className="container mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            <div className="flex flex-col gap-2">
              <h1 className="text-3xl font-bold tracking-tight text-foreground font-display sm:text-4xl">
                {t(title)}
              </h1>
              {subtitle && (
                <p className="text-lg text-muted-foreground max-w-2xl">
                  {t(subtitle)}
                </p>
              )}
            </div>
          </div>
        </header>
      )}

      <main className="flex-1 py-8">
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}
