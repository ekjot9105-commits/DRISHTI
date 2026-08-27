/**
 * PlaceholderPage — Temporary placeholder for pages not yet built.
 * Styled with Tailwind CSS.
 */
export default function PlaceholderPage({ title, description, icon }) {
  return (
    <div className="p-margin-page flex-1 flex flex-col items-center justify-center h-full relative bg-surface">
      <div className="absolute inset-0 pointer-events-none opacity-5" style={{backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)', backgroundSize: '20px 20px'}}></div>
      
      <div className="flex flex-col items-center justify-center bg-surface-container-low border border-outline-variant/30 rounded-sm p-12 max-w-xl text-center shadow-lg relative z-10 w-full">
        <div className="text-6xl mb-6 opacity-30">
          {icon ? icon : <span className="material-symbols-outlined text-6xl" style={{fontVariationSettings: "'FILL' 1"}}>construction</span>}
        </div>
        
        <h2 className="font-headline-md text-on-surface mb-3 tracking-wide uppercase">{title}</h2>
        <p className="font-body-md text-on-surface-variant mb-8 text-sm">{description || 'This feature will be available in a future phase.'}</p>
        
        <div className="bg-surface-container border border-outline-variant/50 rounded-sm px-5 py-3 font-label-md text-on-surface-variant text-xs flex items-center">
          <span className="material-symbols-outlined text-[16px] mr-2 text-primary">assignment</span> 
          Check the Implementation Plan for timeline details
        </div>
      </div>
    </div>
  );
}
