import React from 'react';

interface LogoProps {
    className?: string;
    style?: React.CSSProperties;
    size?: number;
    showText?: boolean;
}

export const Logo: React.FC<LogoProps> = ({ className = "", style, size = 32, showText = true }) => {
    return (
        <div className={`flex items-center gap-2 ${className}`} style={style}>
            <svg
                width={size}
                height={size}
                viewBox="0 0 100 100"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="drop-shadow-sm"
            >
                <defs>
                    <linearGradient id="skyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style={{ stopColor: '#2563eb', stopOpacity: 1 }} />
                        <stop offset="100%" style={{ stopColor: '#10b981', stopOpacity: 1 }} />
                    </linearGradient>
                </defs>

                {/* Background circle */}
                <circle cx="50" cy="50" r="48" fill="url(#skyGrad)" />

                {/* Globe lines */}
                <circle cx="50" cy="50" r="35" fill="none" stroke="white" strokeWidth="2" opacity="0.3" />
                <ellipse cx="50" cy="50" rx="35" ry="15" fill="none" stroke="white" strokeWidth="2" opacity="0.3" />
                <ellipse cx="50" cy="50" rx="15" ry="35" fill="none" stroke="white" strokeWidth="2" opacity="0.3" />

                {/* Sun icon (top right) */}
                <circle cx="70" cy="30" r="6" fill="#fbbf24" />
                <line x1="70" y1="22" x2="70" y2="18" stroke="#fbbf24" strokeWidth="2" />
                <line x1="70" y1="42" x2="70" y2="38" stroke="#fbbf24" strokeWidth="2" />
                <line x1="78" y1="30" x2="82" y2="30" stroke="#fbbf24" strokeWidth="2" />
                <line x1="62" y1="30" x2="58" y2="30" stroke="#fbbf24" strokeWidth="2" />

                {/* Cloud (bottom left) */}
                <path d="M 25 65 Q 20 65 20 70 Q 20 75 25 75 L 38 75 Q 43 75 43 70 Q 43 65 38 65 Q 38 62 35 60 Q 32 58 29 60 Q 28 58 25 60 Z" fill="white" opacity="0.9" />

                {/* Leaf (bottom right) */}
                <path d="M 75 70 Q 75 65 72 62 Q 69 60 66 62 Q 63 65 63 70 L 69 68 Z" fill="#10b981" opacity="0.9" />
            </svg>
            {showText && (
                <span className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-emerald-600">
                    ClimateWise
                </span>
            )}
        </div>
    );
};
