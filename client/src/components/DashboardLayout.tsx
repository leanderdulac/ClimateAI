import { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { NavigationMenu } from "@/components/NavigationMenu";
import { useAuth } from "@/lib/AuthContext";
import { Globe, UserCircle } from "lucide-react";
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      {/* Navigation Header */}
      <nav className="bg-white/95 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="container mx-auto max-w-7xl px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center gap-2 text-xl font-bold text-blue-600 hover:text-blue-700">
                <Globe className="h-6 w-6" />
                {t('app.name')}
              </Link>
              <NavigationMenu />
            </div>
            <div className="flex items-center gap-4">
              <LanguageSwitcher />
              {user ? (
                <div className="flex items-center gap-3">
                  <div className="hidden md:flex items-center gap-2 text-sm">
                    <UserCircle className="h-4 w-4 text-gray-600" />
                    <span className="text-gray-700">{user.name}</span>
                  </div>
                  <Button variant="outline" size="sm" onClick={logout}>
                    {t('nav.logout')}
                  </Button>
                </div>
              ) : (
                <>
                  <Button variant="outline" size="sm" className="hidden md:flex">
                    {t('nav.login')}
                  </Button>
                  <Button size="sm" className="bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700">
                    {t('nav.signup')}
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Page Header */}
      {title && (
        <header className="bg-gradient-to-r from-blue-900 via-purple-900 to-green-900 text-white">
          <div className="container mx-auto max-w-7xl px-6 py-12">
            <div className="text-center">
              <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent mb-4">
                {t(title)}
              </h1>
              {subtitle && (
                <p className="text-xl text-blue-200 max-w-2xl mx-auto">
                  {t(subtitle)}
                </p>
              )}
            </div>
          </div>
        </header>
      )}

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}
