"use client";

import { forwardRef } from "react";
import { motion, HTMLMotionProps } from "framer-motion";

export const MotionButton = forwardRef<HTMLButtonElement, HTMLMotionProps<"button">>(
  function MotionButton({ children, ...props }, ref) {
    return (
      <motion.button ref={ref} whileTap={{ scale: 0.97 }} {...props}>
        {children}
      </motion.button>
    );
  }
);
