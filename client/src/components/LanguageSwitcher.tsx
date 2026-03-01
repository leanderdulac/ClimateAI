import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { useTranslation } from "@/hooks/useTranslation";
import { Globe } from "lucide-react";

const LANGUAGE_LABELS: Record<string, string> = {
    'pt-BR': '🇧🇷 Português',
    'en-US': '🇺🇸 English',
    'es-419': '🇪🇸 Español',
    'zh-CN': '🇨🇳 中文',
};

export function LanguageSwitcher() {
    const { language, setLanguage } = useTranslation();

    return (
        <Select value={language} onValueChange={(value: any) => setLanguage(value)}>
            <SelectTrigger className="w-[155px] bg-transparent border-none focus:ring-0 focus:ring-offset-0">
                <div className="flex items-center gap-2">
                    <Globe className="h-4 w-4 text-gray-500 shrink-0" />
                    <SelectValue placeholder="Language">
                        {LANGUAGE_LABELS[language] || language}
                    </SelectValue>
                </div>
            </SelectTrigger>
            <SelectContent>
                <SelectItem value="pt-BR">🇧🇷 Português (BR)</SelectItem>
                <SelectItem value="en-US">🇺🇸 English (US)</SelectItem>
                <SelectItem value="es-419">🇪🇸 Español</SelectItem>
                <SelectItem value="zh-CN">🇨🇳 中文 (简体)</SelectItem>
            </SelectContent>
        </Select>
    );
}
