import React from 'react';
import Header from './components/Header';
import Benefits from './components/Benefits';
import ReferralForm from './components/ReferralForm';

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-contele-blue relative overflow-x-hidden font-sans selection:bg-contele-accent selection:text-white">
      
      {/* Background Decorative Elements */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-contele-accent rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-[-20%] left-[20%] w-[600px] h-[600px] bg-blue-800 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>
        {/* Mesh pattern overlay */}
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20"></div>
      </div>

      <Header />

      <main className="container mx-auto px-6 pt-24 pb-24 lg:py-0 min-h-screen flex items-center relative z-10">
        <div className="w-full grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          
          {/* Left Column: Benefits & Value Prop */}
          <div className="order-2 lg:order-1">
            <Benefits />
          </div>

          {/* Right Column: Sticky Form */}
          <div className="order-1 lg:order-2 w-full max-w-lg mx-auto lg:mr-0">
             <ReferralForm />
          </div>

        </div>
      </main>

      <footer className="absolute bottom-4 w-full text-center text-blue-200/40 text-xs z-10 pointer-events-none">
        &copy; {new Date().getFullYear()} Contele. Todos os direitos reservados.
      </footer>
    </div>
  );
};

export default App;