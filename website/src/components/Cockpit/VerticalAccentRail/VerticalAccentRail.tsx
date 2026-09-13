import React from 'react';
import { VerticalAccentRailProps } from './VerticalAccentRail.types';

export const VerticalAccentRail: React.FC<VerticalAccentRailProps> = ({
  className = '',
}) => {
  return (
    <aside
      className={`af3-rail-container ${className}`}
      title="AutoFailover 3.0 Vertical Accent"
      aria-label="AutoFailover 3.0 Signature Bezel Rail"
    >
      {/* Top Segment: Fades out gently towards text */}
      <div className="af3-rail-segment af3-rail-top">
        <div className="af3-stripe-cyan"></div>
        <div className="af3-stripe-navy"></div>
        <div className="af3-stripe-red"></div>
      </div>

      {/* Center Protected Label Box: Strictly isolated with 20px padding */}
      <div className="af3-rail-label-box">
        <span className="af3-rail-text">AUTOFAILOVER 3.0</span>
      </div>

      {/* Bottom Segment: Fades in gently after text */}
      <div className="af3-rail-segment af3-rail-bottom">
        <div className="af3-stripe-cyan"></div>
        <div className="af3-stripe-navy"></div>
        <div className="af3-stripe-red"></div>
      </div>
    </aside>
  );
};
