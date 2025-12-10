import React from 'react';
import { CheckCircle, Wallet, Users, Truck } from 'lucide-react';

const Benefits: React.FC = () => {
  return (
    <div className="text-white space-y-8 pr-0 lg:pr-12 pt-12 lg:pt-0">
      <div>
        <span className="inline-block py-1 px-3 rounded-full bg-blue-800/50 border border-blue-700 text-blue-200 text-sm font-medium mb-4 backdrop-blur-sm">
          Programa de Parceiros
        </span>
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
          Indique Contele e <br/>
          <span className="text-contele-accent">Ganhe R$ 300,00</span>
        </h1>
        <p className="mt-6 text-lg md:text-xl text-blue-100 max-w-lg leading-relaxed">
          Conhece empresas que precisam de gestão de frotas ou equipes externas? Indique para a Contele e receba sua recompensa no PIX.
        </p>
      </div>

      <div className="space-y-6">
        <div className="flex items-start gap-4 p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
          <div className="bg-green-500/20 p-3 rounded-lg text-contele-accent">
            <Wallet className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold mb-1">Pagamento via PIX</h3>
            <p className="text-blue-100 text-sm">Sem burocracia. Fechou negócio, você recebe R$ 300 direto na sua conta.</p>
          </div>
        </div>

        <div className="flex items-start gap-4 p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
          <div className="bg-blue-400/20 p-3 rounded-lg text-blue-300">
            <Truck className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold mb-1">Para Frota ou Equipes</h3>
            <p className="text-blue-100 text-sm">
              Indique o <strong>Contele Fleet</strong> para gestão veicular ou <strong>Contele Teams</strong> para produtividade externa.
            </p>
          </div>
        </div>
      </div>

      <div className="pt-4 space-y-6">
        <div className="flex items-center gap-3 text-sm text-blue-200 opacity-80">
          <Users className="w-4 h-4" />
          <span>Mais de <strong>2.000 empresas</strong> confiam na Contele</span>
        </div>

        <div className="bg-white/95 p-3 rounded-xl shadow-lg shadow-black/10 backdrop-blur-sm border border-white/20 w-fit transition-transform hover:scale-105 duration-300">
           <img 
            src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Logo%E2%80%94pix_powered_by_Banco_Central_%28Brazil%2C_2020%29.svg/960px-Logo%E2%80%94pix_powered_by_Banco_Central_%28Brazil%2C_2020%29.svg.png" 
            alt="Pix" 
            className="h-8 w-auto"
          />
        </div>
      </div>
    </div>
  );
};

export default Benefits;