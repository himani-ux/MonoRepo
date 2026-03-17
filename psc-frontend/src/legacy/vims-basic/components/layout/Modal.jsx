import { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

const Modal = ({ children, isOpen }) => {
  const modalRoot = useRef(null);

  useEffect(() => {
    // Create or get the modal root element
    let element = document.getElementById('modal-root');
    if (!element) {
      element = document.createElement('div');
      element.setAttribute('id', 'modal-root');
      document.body.appendChild(element);
    }
    modalRoot.current = element;

    // Cleanup function
    return () => {
      // Optional: Remove modal-root if no modals are open
      // You can skip this if you want to keep the element
    };
  }, []);

  if (!isOpen || !modalRoot.current) return null;

  return createPortal(children, modalRoot.current);
};

export default Modal;