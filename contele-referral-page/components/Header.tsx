import React from 'react';

const Header: React.FC = () => {
  return (
    <nav className="absolute top-0 left-0 w-full z-50 py-6">
      <div className="container mx-auto px-6 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <img 
            src="https://contele.com.br/wp-content/uploads/2024/08/Contele-institucional-1.png" 
            alt="Contele" 
            className="h-12 w-auto brightness-0 invert" 
          />
        </div>
      </div>
    </nav>
  );
};

export default Header;