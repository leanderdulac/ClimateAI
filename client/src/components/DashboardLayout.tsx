import { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { NavigationMenu } from "@/components/NavigationMenu";
import { useAuth } from "@/lib/AuthContext";
import { Globe, LogOut } from "lucide-react";
import { Link } from "react-router-dom";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { useTranslation } from "@/hooks/useTranslation";

interface DashboardLayoutProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
}


export function DashboardLayout({ children, title, subtitle }: DashboardLayoutProps) {
  const { user, logout } = useAuth();
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      {/* Navigation Header - Glass Effect */}
      <nav className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/80 backdrop-blur-md supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center gap-2">
                <div className="rounded-lg bg-primary/10 p-1.5 ring-1 ring-primary/20">
                  <Globe className="h-5 w-5 text-primary" />
                </div>
                <span className="text-lg font-bold tracking-tight text-foreground font-display">
                  {t('app.name')}
                </span>
              </Link>
              <NavigationMenu />
            </div>

            <div className="flex items-center gap-4">
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

      {/* Page Header - Professional Gradient */}
      {title && (
        <header className="border-b border-border bg-muted/30">
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

      {/* Main Content */}
      <main className="flex-1 py-8">
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}
