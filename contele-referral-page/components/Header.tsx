const Header = () => {
  return (
    <nav className="absolute top-0 left-0 w-full z-50 py-4 md:py-6">
      <div className="container mx-auto px-4 md:px-6 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <img
            src="https://contele.com.br/wp-content/uploads/2024/08/Contele-institucional-1.png"
            alt="Contele"
            className="h-12 md:h-14 lg:h-16 w-auto brightness-0 invert"
          />
        </div>
      </div>
    </nav>
  );
};

export default Header;