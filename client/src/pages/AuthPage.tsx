import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/AuthContext";
import { useTranslation } from "@/hooks/useTranslation";
import { Mail, Lock, User, Eye, EyeOff } from "lucide-react";
import { Logo } from "@/components/Logo";

export function AuthPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const navigate = useNavigate();
  const { login, register, isLoading } = useAuth();
  const { t } = useTranslation();

  const [loginData, setLoginData] = useState({
    email: "",
    password: ""
  });

  const [registerData, setRegisterData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    company: "",
    acceptTerms: false
  });

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");

    try {
      if (!loginData.email || !loginData.password) {
        setErrorMessage(t('auth.errors.fillAll'));
        return;
      }

      await login(loginData.email, loginData.password);
      navigate("/dashboard");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : t('auth.errors.loginFailed'));
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");

    try {
      if (!registerData.name || !registerData.email || !registerData.password) {
        setErrorMessage(t('auth.errors.fillRequired'));
        return;
      }

      if (registerData.password !== registerData.confirmPassword) {
        setErrorMessage(t('auth.errors.passwordMatch'));
        return;
      }

      if (!registerData.acceptTerms) {
        setErrorMessage(t('auth.errors.acceptTerms'));
        return;
      }

      await register({
        name: registerData.name,
        email: registerData.email,
        password: registerData.password,
        company: registerData.company
      });

      navigate("/dashboard");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : t('auth.errors.registerFailed'));
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left: Brand / Visual Side */}
      <div className="hidden lg:flex flex-col justify-between bg-muted/30 p-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-mesh opacity-50"></div>
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2672&auto=format&fit=crop')] bg-cover bg-center opacity-10 mix-blend-overlay"></div>

        {/* Logo */}
        <div className="relative z-10">
          <Link to="/" className="inline-flex items-center gap-2">
            <Logo size={32} showText={true} />
          </Link>
        </div>

        <div className="relative z-10 max-w-lg">
          <blockquote className="space-y-6">
            <div className="text-3xl font-display font-bold leading-tight text-foreground">
              "ClimateWise has completely transformed how we assess and mitigate climate risk in our agricultural portfolio."
            </div>
            <footer className="flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-primary/20 flex items-center justify-center font-bold text-primary">
                JD
              </div>
              <div className="text-sm">
                <div className="font-semibold text-foreground">John Davis</div>
                <div className="text-muted-foreground">Risk Manager, AgriCorp Global</div>
              </div>
            </footer>
          </blockquote>
        </div>

        <div className="relative z-10 text-sm text-muted-foreground">
          &copy; 2024 ClimateWise Inc. All rights reserved.
        </div>
      </div>

      {/* Right: Auth Forms */}
      <div className="flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-md space-y-8">
          <div className="lg:hidden text-center mb-8">
            <Link to="/" className="inline-flex items-center justify-center gap-2">
              <Logo size={36} showText={true} />
            </Link>
          </div>

          <div className="flex flex-col space-y-2 text-center">
            <h1 className="text-2xl font-semibold tracking-tight font-display">
              {t('auth.welcome')}
            </h1>
            <p className="text-sm text-muted-foreground">
              {t('auth.welcomeSubtitle')}
            </p>
          </div>

          <Tabs defaultValue="login" className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-8">
              <TabsTrigger value="login">{t('auth.login')}</TabsTrigger>
              <TabsTrigger value="register">{t('auth.register')}</TabsTrigger>
            </TabsList>

            {/* Login Tab */}
            <TabsContent value="login" className="space-y-4">
              {errorMessage && (
                <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md text-destructive text-sm flex items-center gap-2 animate-fade-in">
                  <span className="h-1.5 w-1.5 rounded-full bg-destructive flex-shrink-0" />
                  {errorMessage}
                </div>
              )}
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="login-email">{t('auth.email')}</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="login-email"
                      type="email"
                      placeholder={t('auth.emailPlaceholder')}
                      className="pl-10 h-11"
                      value={loginData.email}
                      onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="login-password">{t('auth.password')}</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="login-password"
                      type={showPassword ? "text" : "password"}
                      placeholder={t('auth.passwordPlaceholder')}
                      className="pl-10 pr-10 h-11"
                      value={loginData.password}
                      onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-3 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <label className="flex items-center space-x-2 text-sm text-muted-foreground hover:text-foreground cursor-pointer transition-colors">
                    <input type="checkbox" className="rounded border-border text-primary focus:ring-primary" />
                    <span>{t('auth.rememberMe')}</span>
                  </label>
                  <Link to="/forgot-password" className="text-sm font-medium text-primary hover:text-primary/80 transition-colors">
                    {t('auth.forgotPassword')}
                  </Link>
                </div>

                <Button type="submit" className="w-full h-11 text-base shadow-lg shadow-primary/20" disabled={isLoading}>
                  {isLoading ? t('auth.loginLoading') : t('auth.loginButton')}
                </Button>
              </form>
            </TabsContent>

            {/* Register Tab */}
            <TabsContent value="register" className="space-y-4">
              {errorMessage && (
                <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md text-destructive text-sm flex items-center gap-2 animate-fade-in">
                  <span className="h-1.5 w-1.5 rounded-full bg-destructive flex-shrink-0" />
                  {errorMessage}
                </div>
              )}
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="register-name">{t('auth.fullName')}</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="register-name"
                      type="text"
                      placeholder={t('auth.fullNamePlaceholder')}
                      className="pl-10 h-11"
                      value={registerData.name}
                      onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="register-email">{t('auth.email')}</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="register-email"
                      type="email"
                      placeholder={t('auth.emailPlaceholder')}
                      className="pl-10 h-11"
                      value={registerData.email}
                      onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="register-company">{t('auth.company')}</Label>
                  <Input
                    id="register-company"
                    type="text"
                    placeholder={t('auth.companyPlaceholder')}
                    className="h-11"
                    value={registerData.company}
                    onChange={(e) => setRegisterData({ ...registerData, company: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="register-password">{t('auth.password')}</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="register-password"
                      type={showPassword ? "text" : "password"}
                      placeholder={t('auth.passwordPlaceholder')}
                      className="pl-10 pr-10 h-11"
                      value={registerData.password}
                      onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-3 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="register-confirm-password">{t('auth.confirmPassword')}</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="register-confirm-password"
                      type={showPassword ? "text" : "password"}
                      placeholder={t('auth.passwordPlaceholder')}
                      className="pl-10 pr-10 h-11"
                      value={registerData.confirmPassword}
                      onChange={(e) => setRegisterData({ ...registerData, confirmPassword: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <div className="flex items-start space-x-2 pt-2">
                  <input
                    type="checkbox"
                    id="accept-terms"
                    className="mt-1 rounded border-border text-primary focus:ring-primary"
                    checked={registerData.acceptTerms}
                    onChange={(e) => setRegisterData({ ...registerData, acceptTerms: e.target.checked })}
                    required
                  />
                  <label htmlFor="accept-terms" className="text-sm text-muted-foreground leading-none">
                    {t('auth.acceptTerms')}{" "}
                    <Link to="/terms" className="text-primary hover:text-primary/80 transition-colors">
                      {t('auth.termsLink')}
                    </Link>{" "}
                    {t('auth.and')}{" "}
                    <Link to="/privacy" className="text-primary hover:text-primary/80 transition-colors">
                      {t('auth.privacyLink')}
                    </Link>
                  </label>
                </div>

                <Button type="submit" className="w-full h-11 text-base shadow-lg shadow-primary/20" disabled={isLoading}>
                  {isLoading ? t('auth.registerLoading') : t('auth.registerButton')}
                </Button>
              </form>
            </TabsContent>
          </Tabs>

          <div className="text-center text-sm text-muted-foreground">
            <p>
              {t('auth.needHelp')}{" "}
              <Link to="/support" className="text-primary hover:text-primary/80 font-medium transition-colors">
                {t('auth.contact')}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
