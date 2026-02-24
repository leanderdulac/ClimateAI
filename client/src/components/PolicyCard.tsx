import { useTranslation } from '@/hooks/useTranslation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckCircle, AlertTriangle, XCircle, Shield } from "lucide-react";

export type PolicyStatus = 'recommended' | 'acceptable' | 'caution' | 'rejected';

export interface PolicyCardProps {
    title: string;
    description: string;
    premium: number;
    coverage: number;
    status: PolicyStatus;
    metrics: {
        profitMargin: number;
        roi: number;
        riskScore: number;
    };
    tags?: string[];
    onSelect?: () => void;
}

export function PolicyCard({
    title,
    description,
    premium,
    coverage,
    status,
    metrics,
    tags = [],
    onSelect
}: PolicyCardProps) {
    const { t } = useTranslation();

    const getStatusConfig = (status: PolicyStatus) => {
        switch (status) {
            case 'recommended':
                return {
                    color: 'bg-green-50 border-green-200',
                    icon: <CheckCircle className="h-5 w-5 text-green-600" />,
                    badge: 'bg-green-100 text-green-700',
                    label: t('policy.status.recommended')
                };
            case 'acceptable':
                return {
                    color: 'bg-blue-50 border-blue-200',
                    icon: <Shield className="h-5 w-5 text-blue-600" />,
                    badge: 'bg-blue-100 text-blue-700',
                    label: t('policy.status.acceptable')
                };
            case 'caution':
                return {
                    color: 'bg-yellow-50 border-yellow-200',
                    icon: <AlertTriangle className="h-5 w-5 text-yellow-600" />,
                    badge: 'bg-yellow-100 text-yellow-700',
                    label: t('policy.status.caution')
                };
            case 'rejected':
                return {
                    color: 'bg-red-50 border-red-200',
                    icon: <XCircle className="h-5 w-5 text-red-600" />,
                    badge: 'bg-red-100 text-red-700',
                    label: t('policy.status.rejected')
                };
        }
    };

    const config = getStatusConfig(status);

    return (
        <Card className={`border-2 transition-all hover:shadow-md ${config.color}`}>
            <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                    <div className="space-y-1">
                        <div className="flex items-center gap-2">
                            {config.icon}
                            <Badge variant="secondary" className={config.badge}>
                                {config.label}
                            </Badge>
                        </div>
                        <CardTitle className="text-lg font-bold text-gray-900 mt-2">
                            {title}
                        </CardTitle>
                    </div>
                    <div className="text-right">
                        <div className="text-2xl font-bold text-gray-900">
                            R$ {premium.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </div>
                        <div className="text-xs text-gray-500">{t('policy.labels.annualPremium')}</div>
                    </div>
                </div>
                <CardDescription className="text-gray-600 mt-2">
                    {description}
                </CardDescription>
            </CardHeader>
            <CardContent className="pb-2">
                <div className="grid grid-cols-3 gap-4 py-4 border-t border-b border-gray-200/50 my-2">
                    <div className="text-center">
                        <div className="text-xs text-gray-500 mb-1">{t('policy.labels.margin')}</div>
                        <div className={`font-bold ${metrics.profitMargin > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {metrics.profitMargin.toFixed(1)}%
                        </div>
                    </div>
                    <div className="text-center border-l border-gray-200/50">
                        <div className="text-xs text-gray-500 mb-1">{t('policy.labels.roi')}</div>
                        <div className="font-bold text-blue-600">
                            {metrics.roi.toFixed(1)}x
                        </div>
                    </div>
                    <div className="text-center border-l border-gray-200/50">
                        <div className="text-xs text-gray-500 mb-1">{t('policy.labels.risk')}</div>
                        <div className={`font-bold ${metrics.riskScore > 7 ? 'text-red-600' : metrics.riskScore > 4 ? 'text-yellow-600' : 'text-green-600'}`}>
                            {metrics.riskScore}/10
                        </div>
                    </div>
                </div>

                {tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-4">
                        {tags.map((tag, i) => (
                            <Badge key={i} variant="outline" className="bg-white/50 text-xs">
                                {tag}
                            </Badge>
                        ))}
                    </div>
                )}
            </CardContent>
            <CardFooter className="pt-2">
                <Button
                    className="w-full bg-white hover:bg-gray-50 text-gray-900 border border-gray-200"
                    variant="outline"
                    onClick={onSelect}
                >
                    {t('policy.actions.viewDetails')}
                </Button>
            </CardFooter>
        </Card>
    );
}
