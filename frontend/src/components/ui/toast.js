import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import * as React from "react";
export const Toast = React.forwardRef(({ id, title, description, action, open, onOpenChange, className, children, ...props }, ref) => {
    return (_jsxs("div", { ref: ref, role: "status", "aria-live": "polite", className: className, ...props, children: [title && _jsx("div", { className: "font-semibold", children: title }), description && _jsx("div", { className: "text-sm opacity-90", children: description }), action, children] }));
});
Toast.displayName = "Toast";
