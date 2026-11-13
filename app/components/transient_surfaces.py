import reflex as rx


def transient_surface_listeners() -> rx.Component:
    return rx.script("""
        (() => {
          if (window.gahTransientSurfaces) return;
          window.gahTransientSurfaces = true;
          const surfaces = ['gah-forum-dropdown', 'gah-event-calendar'];
          const closeOutside = (target) => surfaces.forEach(id => {
            const wrapper = document.getElementById(id);
            if (wrapper && !wrapper.contains(target)) {
              document.getElementById(id + '-close')?.click();
            }
          });
          document.addEventListener('pointerdown', e => closeOutside(e.target));
          document.addEventListener('focusout', e => {
            if (e.relatedTarget) closeOutside(e.relatedTarget);
            else setTimeout(() => closeOutside(document.activeElement), 0);
          });
          document.addEventListener('scroll', e => {
            if (e.target instanceof Element && e.target.matches('.gah-member-section')) {
              surfaces.forEach(id => document.getElementById(id + '-close')?.click());
            }
          }, true);
        })();
    """)
