import { useState, useEffect } from 'react';
import { motion } from 'motion/react';

const competitions = [
  { name: 'FIFA World Cup', logo: '/leagues/world-cup.svg', alt: 'FIFA World Cup' },
  { name: 'Premier League', logo: '/leagues/premier-league.svg', alt: 'Premier League' },
  { name: 'La Liga', logo: '/leagues/la-liga-seeklogo.png', alt: 'La Liga' },
  { name: 'Bundesliga', logo: '/leagues/bundesliga.png', alt: 'Bundesliga' },
  { name: 'Champions League', logo: '/leagues/champions-league.svg', alt: 'Champions League' },
  { name: 'Europa League', logo: '/leagues/europa-league.svg', alt: 'Europa League' },
  { name: 'Serie A', logo: '/leagues/serie-a.svg', alt: 'Serie A' },
];

interface CompetitionSelectorProps {
  isFloating?: boolean;
}

export default function CompetitionSelector({ isFloating = false }: CompetitionSelectorProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      className="bg-white/50 backdrop-blur-md border border-[#1C1B17]/8 rounded-xl shadow-[0_8px_30px_rgba(28,27,23,0.03)] overflow-hidden transition-all duration-300 hover:shadow-[0_12px_40px_rgba(28,27,23,0.06)] hover:border-[#1C1B17]/15"
    >
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-7 divide-x divide-[#1C1B17]/6">
        {competitions.map((comp, index) => (
          <motion.div
            key={comp.name}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 + index * 0.05, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="relative group px-4 py-4 flex flex-col items-center justify-center cursor-pointer hover:bg-[#1C1B17]/2 transition-all duration-300"
            whileHover={{ y: -3 }}
          >
            <div className="w-8 h-8 md:w-9 md:h-9 flex items-center justify-center mb-2">
              <img 
                src={comp.logo} 
                alt={comp.alt} 
                className="object-contain max-w-full max-h-full transition-transform duration-300 group-hover:scale-105"
                loading="lazy"
                onError={(e) => console.error(`Failed to load logo: ${comp.logo}`, e)}
              />
            </div>
            <span className="font-serif text-[#1C1B17]/80 group-hover:text-[#1C1B17] uppercase tracking-wider text-[9px] text-center line-clamp-1 transition-colors duration-250">
              {comp.name}
            </span>
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#3a5c2d] transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-center opacity-0 group-hover:opacity-100" />
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
