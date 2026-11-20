import reflex as rx

from app.interface_i18n import ui

DRAWER_CLASS = "gah-search-drawer pointer-events-auto fixed right-2 bottom-[calc(3.875rem+env(safe-area-inset-bottom))] z-30 flex w-[calc(100vw-1rem)] max-w-[23.75rem] max-h-[calc(100dvh-5rem-env(safe-area-inset-bottom))] min-h-0 flex-col overflow-y-auto overscroll-contain rounded-tl-2xl border-0 bg-white/80 p-3 font-['Inter'] text-[#404040] backdrop-blur-sm"
CONTENT_CLASS = "flex w-full min-w-0 flex-col gap-1.5 font-['Inter'] [&_button]:text-sm [&_input]:text-sm [&_select]:text-sm [&_button_span]:text-sm [&_label]:text-[13px] [&_p]:text-xs [&_span[role=status]]:text-[13px]"
HEADER_CLASS = "relative flex min-h-8 w-full min-w-0 flex-row items-start justify-start gap-1.5 pr-10"
HEADER_TOGGLES_CLASS = "flex min-w-0 flex-1 flex-row flex-wrap items-center justify-start gap-1.5 [direction:ltr]"
CLOSE_CLASS = "absolute right-0 top-0 flex size-8 shrink-0 items-center justify-center rounded-full bg-[#fff7e8] text-[#b86e08] transition-colors hover:bg-[#ffedcc] focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]"
BODY_CLASS = "mt-1 flex w-full min-w-0 flex-col gap-1.5"
LOCATION_SPACING_CLASS = "mt-2 w-full ps-[5px]"
DISTANCE_SPACING_CLASS = "mt-1 w-full ps-[5px]"
FOOTER_CLASS = "flex flex-wrap items-center justify-between gap-1"
FOOTER_BUTTON_CLASS = "w-fit flex items-center gap-1.5 rounded-lg px-2 py-1 text-[11px] font-semibold text-[#6b7280] transition-colors enabled:hover:bg-white enabled:hover:text-[#b86e08] disabled:opacity-60 disabled:cursor-not-allowed focus:outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]/40"
FIELD_CLASS = "gah-filter-field flex h-10 w-full items-center gap-2 rounded-xl border border-gray-300 bg-white px-3 text-sm font-medium text-[#404040] outline-hidden transition-colors focus:border-[#fba922] focus:ring-2 focus:ring-[#fba922]/30"
SELECT_CLASS = "gah-filter-field h-10 w-full appearance-none cursor-pointer rounded-xl border border-gray-300 bg-white px-3 pr-9 text-sm font-medium text-[#404040] outline-hidden transition-colors focus:border-[#fba922] focus:ring-2 focus:ring-[#fba922]/30"
SEARCH_INPUT_CLASS = "gah-search-inner gah-filter-field min-w-0 flex-1 h-10 rounded-xl border-0 bg-transparent px-3 text-sm font-medium text-[#404040] placeholder:text-[#404040] outline-hidden focus-visible:outline-none!"
SEARCH_FORM_CLASS = "gah-search-form flex h-10 w-full items-center rounded-xl border border-gray-300 bg-white focus-within:border-[#fba922]"
MODE_GROUP_CLASS = "gah-segment-group flex min-w-0 w-fit max-w-full flex-wrap items-center gap-0 rounded-full border border-[#d4d4d4] bg-white p-0"
MODE_ON_CLASS = "gah-segment-control flex min-h-[31px] min-w-0 items-center justify-center rounded-full bg-[#fba922] px-[11px] text-sm font-bold text-[#000000] [overflow-wrap:anywhere] focus-visible:ring-2 focus-visible:ring-[#e08b12]"
MODE_OFF_CLASS = "gah-segment-control flex min-h-[31px] min-w-0 items-center justify-center rounded-full px-[11px] text-sm font-bold text-[#404040] [overflow-wrap:anywhere] transition-colors hover:text-black focus-visible:ring-2 focus-visible:ring-[#e08b12]"
VIEW_GROUP_CLASS = "gah-segment-group flex h-7 shrink-0 items-center gap-0 rounded-full border border-[#d4d4d4] bg-white p-0"
VIEW_ON_CLASS = "gah-segment-control flex size-7 shrink-0 items-center justify-center rounded-full bg-[#fba922] text-[#000000] focus-visible:ring-2 focus-visible:ring-[#e08b12]"
VIEW_OFF_CLASS = "gah-segment-control flex size-7 shrink-0 items-center justify-center rounded-full text-[#404040] transition-colors hover:text-[#000000] focus-visible:ring-2 focus-visible:ring-[#e08b12]"
LOCATION_ROW_CLASS = (
    "flex w-full flex-wrap items-center justify-start gap-x-2 gap-y-1.5"
)
LOCATION_LABEL_CLASS = "text-xs font-semibold text-[#404040]"
LOCATION_GROUP_CLASS = "gah-segment-group flex min-w-0 flex-1 flex-row flex-wrap items-stretch gap-1 rounded-xl bg-white/80 p-0.5"
LOCATION_ON_CLASS = "gah-segment-control flex flex-1 min-w-0 basis-auto items-center justify-center gap-1 rounded-lg bg-[#fba922] px-2 py-1.5 text-[11px] font-bold text-[#111827] transition-colors disabled:opacity-60 outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]/40"
LOCATION_OFF_CLASS = "gah-segment-control flex flex-1 min-w-0 basis-auto items-center justify-center gap-1 rounded-lg bg-transparent px-2 py-1.5 text-[11px] font-bold text-[#404040] transition-colors hover:bg-white disabled:opacity-60 outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]/40"
RANGE_CLASS = "gah-distance-range -translate-y-1 h-8 w-full min-w-0 touch-none cursor-pointer appearance-none bg-transparent outline-hidden focus-visible:ring-2 focus-visible:ring-[#e08b12]"


def distance_row(label: str | rx.Var[str], input_id: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            ui("1 km"), class_name="shrink-0 text-[11px] font-bold text-black"
        ),
        rx.el.label(
            ui("Distance"),
            rx.el.span(
                label,
                role="status",
                aria_live="polite",
                class_name="text-[#e08b12]",
            ),
            html_for=input_id,
            class_name="min-w-0 flex-1 text-center text-[11px] font-bold text-black [overflow-wrap:anywhere]",
        ),
        rx.el.span(
            ui("Any"), class_name="shrink-0 text-[11px] font-bold text-black"
        ),
        class_name="mb-1 flex w-full min-w-0 items-baseline justify-between gap-1",
    )
