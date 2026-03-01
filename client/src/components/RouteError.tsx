import { useRouteError, isRouteErrorResponse, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

export function RouteError() {
    const error = useRouteError();
    const navigate = useNavigate();

    let errorMessage = "Ocorreu um erro inesperado ao carregar a página.";
    let errorStatus = "";

    if (isRouteErrorResponse(error)) {
        errorStatus = `${error.status} ${error.statusText}`;
        errorMessage = error.data?.message || error.statusText;
    } else if (error instanceof Error) {
        errorMessage = error.message;
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
            <div className="max-w-md w-full glass-card p-8 border-red-100 shadow-2xl text-center space-y-6">
                <div className="mx-auto w-16 h-16 rounded-full bg-red-100 flex items-center justify-center">
                    <AlertTriangle className="h-8 w-8 text-red-600" />
                </div>

                <div className="space-y-2">
                    <h2 className="text-2xl font-bold text-foreground">Oops! Algo deu errado</h2>
                    <p className="text-muted-foreground leading-relaxed">
                        {errorMessage}
                    </p>
                    {errorStatus && (
                        <div className="text-xs font-mono text-muted-foreground/60">
                            Status: {errorStatus}
                        </div>
                    )}
                </div>

                <div className="flex flex-col gap-3 pt-4">
                    <Button
                        onClick={() => window.location.reload()}
                        className="w-full h-12 gap-2"
                    >
                        <RefreshCw className="h-4 w-4" />
                        Tentar Novamente
                    </Button>
                    <Button
                        variant="outline"
                        onClick={() => navigate('/')}
                        className="w-full h-12 gap-2"
                    >
                        <Home className="h-4 w-4" />
                        Voltar ao Início
                    </Button>
                </div>
            </div>
        </div>
    );
}
