import { motion } from "framer-motion";
import AuthHero from "./AuthHero.jsx";
import PageBackdrop from "./ui/PageBackdrop.jsx";

function AuthLayout({ children }) {
  return (
    <div className="relative grid min-h-screen lg:grid-cols-2">
      <PageBackdrop variant="cream" />
      <AuthHero />
      <div className="relative flex items-center justify-center bg-mesh-cream px-6 py-12 lg:px-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
          className="glass-card w-full max-w-md !p-8"
        >
          {children}
        </motion.div>
      </div>
    </div>
  );
}

export default AuthLayout;
