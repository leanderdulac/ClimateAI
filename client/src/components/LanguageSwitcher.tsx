import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { useTranslation } from "@/hooks/useTranslation";
import { Globe } from "lucide-react";

export function LanguageSwitcher() {
    const { language, setLanguage } = useTranslation();

    return (
        <Select value={language} onValueChange={(value: any) => setLanguage(value)}>
            <SelectTrigger className="w-[140px] bg-transparent border-none focus:ring-0 focus:ring-offset-0">
                <div className="flex items-center gap-2">
                    <Globe className="h-4 w-4 text-gray-500" />
                    <SelectValue placeholder="Language" />
                </div>
            </SelectTrigger>
            <SelectContent>
                <SelectItem value="pt-BR">Português (BR)</SelectItem>
                <SelectItem value="en-US">English (US)</SelectItem>
            </SelectContent>
        </Select>
    );
}
