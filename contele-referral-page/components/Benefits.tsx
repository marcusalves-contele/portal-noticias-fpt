import { Wallet, Users, Truck, Shield } from 'lucide-react';

const Benefits = () => {
  return (
    <div className="text-white space-y-6 md:space-y-8 pr-0 lg:pr-12 pt-6 md:pt-20 lg:pt-12">
      <div>
        <span className="inline-block py-1.5 md:py-2 px-3 md:px-4 rounded-full bg-green-500/20 border border-green-400/50 text-green-300 text-sm md:text-base font-semibold mb-3 md:mb-4 backdrop-blur-sm animate-neon-pulse">
          Indique e Ganhe no PIX
        </span>
        <h1 className="text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-extrabold tracking-tight leading-tight">
          Indique e <br/>
          <span className="text-contele-accent">Ganhe R$ 300,00</span>
        </h1>
        <p className="mt-4 md:mt-6 text-lg md:text-xl lg:text-2xl text-blue-100 max-w-lg leading-relaxed">
          Indique empresas que têm <strong>veículos</strong> ou <strong>pessoas trabalhando na rua</strong>. Se a sua indicação fechar com a Contele, você recebe um PIX!
        </p>
      </div>

      {/* Destaque: Prova Social */}
      <div className="bg-gradient-to-r from-green-500/20 to-blue-500/20 p-4 md:p-5 rounded-2xl border border-green-400/30 backdrop-blur-sm">
        <div className="flex items-center gap-3 md:gap-4">
          <div className="bg-green-500/30 p-2 md:p-3 rounded-full flex-shrink-0">
            <Users className="w-6 h-6 md:w-8 md:h-8 text-green-300" />
          </div>
          <div>
            <p className="text-base md:text-lg lg:text-xl font-bold text-white leading-snug">
              Mais de <span className="text-contele-accent">2.000 empresas</span> confiam na Contele
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-4 md:space-y-5">
        <div className="flex items-start gap-3 md:gap-4 p-4 md:p-5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
          <div className="bg-green-500/20 p-2 md:p-3 rounded-lg text-contele-accent flex-shrink-0">
            <Wallet className="w-6 h-6 md:w-7 md:h-7" />
          </div>
          <div>
            <h3 className="text-lg md:text-xl lg:text-2xl font-bold mb-1 md:mb-2">Pagamento via PIX</h3>
            <p className="text-blue-100 text-sm md:text-base lg:text-lg">Sem burocracia. Fechou negócio, você recebe R$ 300 direto na sua conta.</p>
          </div>
        </div>

        <div className="flex items-start gap-3 md:gap-4 p-4 md:p-5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
          <div className="bg-blue-400/20 p-2 md:p-3 rounded-lg text-blue-300 flex-shrink-0">
            <Truck className="w-6 h-6 md:w-7 md:h-7" />
          </div>
          <div>
            <h3 className="text-lg md:text-xl lg:text-2xl font-bold mb-1 md:mb-2">Para Frotas ou Equipes Externas</h3>
            <p className="text-blue-100 text-sm md:text-base lg:text-lg">
              Indique o <strong>Contele Fleet</strong> para gestão de frotas ou <strong>Contele Teams</strong> para equipes externas.
            </p>
          </div>
        </div>
      </div>

      {/* Seção de Credibilidade - Versão Compacta */}
      <div className="pt-4 md:pt-6 border-t border-white/10">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 opacity-60 hover:opacity-80 transition-opacity">
          {/* Texto 22 anos com ícone */}
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-blue-300 flex-shrink-0" />
            <span className="text-xs md:text-sm text-blue-200">23 anos no mercado</span>
          </div>

          {/* Logos dos parceiros - inline e pequenos */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-blue-300/70 hidden md:inline">|</span>
            <div className="flex items-center gap-3">
              <img src="https://contele.com.br/img/parceiros/anatel.svg" alt="Anatel" className="h-4 md:h-5 w-auto brightness-0 invert opacity-80" />
              <img src="https://contele.com.br/img/parceiros/aws.png" alt="Amazon" className="h-4 md:h-5 w-auto brightness-0 invert opacity-80" />
              <img src="https://contele.com.br/img/parceiros/google-maps.svg" alt="Google Maps" className="h-4 md:h-5 w-auto brightness-0 invert opacity-80" />
              <img src="https://contele.com.br/img/parceiros/google-cloud.svg" alt="Google Cloud" className="h-4 md:h-5 w-auto brightness-0 invert opacity-80" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Benefits;