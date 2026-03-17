  
const Footer = ({ customContent }) => {
  if (customContent) {
    return customContent;
  }

  return (
    <footer className="bg-gray-200 text-black py-4">
            <div className="container mx-auto px-4 text-center text-sm">
                <p>&copy; {new Date().getFullYear()} KSM Circulars. All rights reserved.</p>
                <div className="mt-2 space-x-4">
                    <a href="#terms" className="hover:text-red-500">Terms of Service</a>
                    <a href="#privacy" className="hover:text-red-500">Privacy Policy</a>
                    <a href="#support" className="hover:text-red-500">Support</a>
                </div>
            </div>
        </footer>
  );
};

export default Footer;
